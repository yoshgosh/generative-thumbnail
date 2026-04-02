import json
import os
from urllib.parse import quote, unquote

import azure.functions as func
from pydantic import ValidationError

from src.blob_storage import (
    get_blob_png_bytes,
    delete_old_blobs_for_algorithm,
    list_recent_shared_items,
    save_png_to_imgs_storage,
    to_text_token,
)
from src.image_generator import DEFAULT_ALGORITHM_NAME, list_algorithms
from src.api_models import GenerateRequest
from src.thumbnail_service import (
    create_thumbnail_png_bytes,
    normalize_text_position,
    resolve_dimensions,
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
DEFAULT_MAX_IMAGES_PER_ALGORITHM = 50
DEFAULT_HISTORY_LIMIT = 12
MAX_HISTORY_LIMIT = 100


def _content_disposition(filename_base: str) -> str:
    encoded = quote(f"{filename_base}.png", safe="")
    return f"inline; filename=\"thumbnail.png\"; filename*=UTF-8''{encoded}"


def _read_payload(req: func.HttpRequest) -> dict:
    payload: dict = {}
    for key in (
        "title",
        "text",
        "text_position",
        "font_scale",
        "size",
        "width",
        "height",
        "algorithm",
        "save",
    ):
        value = req.params.get(key)
        if value is not None:
            payload[key] = value

    if req.get_body():
        try:
            body = req.get_json()
            if isinstance(body, dict):
                payload.update(body)
        except ValueError:
            pass
    return payload


@app.route(route="generate", methods=["GET", "POST"])
def generate(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = _read_payload(req)
        try:
            request_model = GenerateRequest.model_validate(payload)
        except ValidationError as exc:
            return func.HttpResponse(
                json.dumps({"error": "validation_error", "details": exc.errors()}),
                status_code=400,
                mimetype="application/json",
            )

        algorithm_names = {spec.name for spec in list_algorithms()}
        algorithm_name = request_model.algorithm or DEFAULT_ALGORITHM_NAME
        if algorithm_name not in algorithm_names:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "invalid algorithm",
                        "available_algorithms": sorted(algorithm_names),
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        png_bytes = create_thumbnail_png_bytes(
            title=request_model.title,
            draw_text=request_model.text,
            text_position=request_model.text_position,
            font_scale=request_model.font_scale,
            size=request_model.size,
            width=request_model.width,
            height=request_model.height,
            algorithm_name=str(algorithm_name),
        )

        if request_model.save:
            resolved_width, resolved_height = resolve_dimensions(
                size=request_model.size,
                width=request_model.width,
                height=request_model.height,
            )
            normalized_text_position = normalize_text_position(request_model.text_position)
            text_token = to_text_token(
                draw_text=request_model.text,
                normalized_text_position=normalized_text_position,
            )
            save_png_to_imgs_storage(
                png_bytes=png_bytes,
                algorithm_name=str(algorithm_name),
                title=request_model.title,
                width=resolved_width,
                height=resolved_height,
                text_token=text_token,
            )

        return func.HttpResponse(
            body=png_bytes,
            status_code=200,
            mimetype="image/png",
            headers={
                "Content-Disposition": _content_disposition(request_model.title),
                "Cache-Control": "no-store",
            },
        )
    except Exception as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=500,
            mimetype="application/json",
        )


def _resolve_max_images_per_algorithm() -> int:
    raw = os.getenv("MAX_IMAGES_PER_ALGORITHM", str(DEFAULT_MAX_IMAGES_PER_ALGORITHM))
    try:
        return max(0, int(raw))
    except ValueError:
        return DEFAULT_MAX_IMAGES_PER_ALGORITHM


def _resolve_history_limit(req: func.HttpRequest) -> int:
    raw = req.params.get("limit")
    if raw is None:
        return DEFAULT_HISTORY_LIMIT
    try:
        parsed = int(raw)
    except ValueError:
        return DEFAULT_HISTORY_LIMIT
    return max(1, min(parsed, MAX_HISTORY_LIMIT))


@app.route(route="history", methods=["GET"])
def history(req: func.HttpRequest) -> func.HttpResponse:
    try:
        limit = _resolve_history_limit(req)
        items = list_recent_shared_items(limit=limit)
        return func.HttpResponse(
            json.dumps({"items": items, "limit": limit, "count": len(items)}),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="history/image", methods=["GET"])
def history_image(req: func.HttpRequest) -> func.HttpResponse:
    raw_blob_name = req.params.get("blob_name", "")
    blob_name = unquote(raw_blob_name).strip()
    if not blob_name or "/" not in blob_name or not blob_name.lower().endswith(".png"):
        return func.HttpResponse(
            json.dumps({"error": "invalid blob_name"}),
            status_code=400,
            mimetype="application/json",
        )
    try:
        png_bytes = get_blob_png_bytes(blob_name)
        return func.HttpResponse(
            body=png_bytes,
            status_code=200,
            mimetype="image/png",
            headers={"Cache-Control": "public, max-age=60"},
        )
    except Exception as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=500,
            mimetype="application/json",
        )


@app.timer_trigger(
    schedule="%CLEANUP_SCHEDULE%",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def cleanup_old_images(timer: func.TimerRequest) -> None:
    max_count = _resolve_max_images_per_algorithm()
    if max_count <= 0:
        return

    deleted_total = 0
    for spec in list_algorithms():
        deleted_count = delete_old_blobs_for_algorithm(spec.name, max_count=max_count)
        deleted_total += deleted_count
    print(f"cleanup_old_images completed. deleted_total={deleted_total}, max_count={max_count}")
