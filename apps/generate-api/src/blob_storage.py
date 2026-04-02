"""
Blob Storage 保存ロジック
"""

import os
import re
from collections.abc import Iterable

from azure.storage.blob import BlobServiceClient

DEFAULT_IMGS_CONTAINER = "images"

TEXT_TOKEN_MAP = {
    "center": "c",
    "top-left": "tl",
    "top-right": "tr",
    "bottom-left": "bl",
    "bottom-right": "br",
}


def to_text_token(draw_text: bool, normalized_text_position: str) -> str:
    if not draw_text:
        return "n"
    return TEXT_TOKEN_MAP.get(normalized_text_position, "c")


def sanitize_title_for_blob_name(title: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", title.strip())
    safe = re.sub(r"\s+", "_", safe)
    return safe or "thumbnail"


def build_blob_name(
    algorithm_name: str,
    title: str,
    width: int,
    height: int,
    text_token: str,
) -> str:
    safe_title = sanitize_title_for_blob_name(title)
    filename = f"{safe_title}_w{width}_h{height}_{text_token}.png"
    return f"{algorithm_name}/{filename}"


def save_png_to_imgs_storage(
    *,
    png_bytes: bytes,
    algorithm_name: str,
    title: str,
    width: int,
    height: int,
    text_token: str,
) -> str:
    connection_string = os.getenv("AZURE_IMGS_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise RuntimeError("AZURE_IMGS_STORAGE_CONNECTION_STRING is not set")

    container_name = os.getenv("AZURE_IMGS_STORAGE_CONTAINER", DEFAULT_IMGS_CONTAINER)
    blob_name = build_blob_name(
        algorithm_name=algorithm_name,
        title=title,
        width=width,
        height=height,
        text_token=text_token,
    )

    service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(png_bytes, overwrite=True)
    return blob_name


def _get_container_client():
    connection_string = os.getenv("AZURE_IMGS_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise RuntimeError("AZURE_IMGS_STORAGE_CONNECTION_STRING is not set")

    container_name = os.getenv("AZURE_IMGS_STORAGE_CONTAINER", DEFAULT_IMGS_CONTAINER)
    service_client = BlobServiceClient.from_connection_string(connection_string)
    return service_client.get_container_client(container_name)


def list_algorithm_blob_names_sorted_newest_first(algorithm_name: str) -> list[str]:
    container_client = _get_container_client()
    prefix = f"{algorithm_name}/"
    blobs: Iterable = container_client.list_blobs(name_starts_with=prefix)
    sorted_blobs = sorted(
        blobs,
        key=lambda b: b.last_modified or 0,
        reverse=True,
    )
    return [blob.name for blob in sorted_blobs]


def delete_old_blobs_for_algorithm(algorithm_name: str, max_count: int) -> int:
    if max_count < 0:
        max_count = 0

    container_client = _get_container_client()
    blob_names = list_algorithm_blob_names_sorted_newest_first(algorithm_name)
    delete_targets = blob_names[max_count:]
    for blob_name in delete_targets:
        container_client.delete_blob(blob_name)
    return len(delete_targets)
