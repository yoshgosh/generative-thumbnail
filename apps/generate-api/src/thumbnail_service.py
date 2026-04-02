"""
サムネイル生成の共通サービスロジック
"""

from io import BytesIO
from pathlib import Path

from PIL import Image

from src.image_generator import DEFAULT_ALGORITHM_NAME, generate_image
from src.text_renderer import draw_title_text

DEFAULT_SIZE = 500
DEFAULT_FONT_SCALE = 0.05
DEFAULT_TEXT_POSITION = "center"
MIN_SIZE = 16

TEXT_POSITION_MAP = {
    "c": "center",
    "tl": "top-left",
    "tr": "top-right",
    "bl": "bottom-left",
    "br": "bottom-right",
}


def resolve_dimensions(
    size: int,
    width: int | None,
    height: int | None,
) -> tuple[int, int]:
    """画像サイズを確定する（width/height が指定されたら優先）。"""
    base_size = max(MIN_SIZE, int(size))
    resolved_width = max(MIN_SIZE, int(width if width is not None else base_size))
    resolved_height = max(MIN_SIZE, int(height if height is not None else base_size))
    return resolved_width, resolved_height


def normalize_text_position(text_position: str) -> str:
    return TEXT_POSITION_MAP.get(text_position.lower(), text_position.lower())


def create_thumbnail_image(
    title: str,
    draw_text: bool = False,
    text_position: str = DEFAULT_TEXT_POSITION,
    font_scale: float = DEFAULT_FONT_SCALE,
    size: int = DEFAULT_SIZE,
    width: int | None = None,
    height: int | None = None,
    algorithm_name: str = DEFAULT_ALGORITHM_NAME,
) -> Image.Image:
    """サムネイル画像オブジェクトを生成して返す。"""
    resolved_width, resolved_height = resolve_dimensions(
        size=size,
        width=width,
        height=height,
    )
    normalized_position = normalize_text_position(text_position)

    img = generate_image(
        title=title,
        width=resolved_width,
        height=resolved_height,
        algorithm_name=algorithm_name,
    )

    if draw_text:
        img = draw_title_text(
            img=img,
            title=title,
            text_position=normalized_position,
            font_scale=font_scale,
        )
    return img


def create_thumbnail_png_bytes(
    title: str,
    draw_text: bool = False,
    text_position: str = DEFAULT_TEXT_POSITION,
    font_scale: float = DEFAULT_FONT_SCALE,
    size: int = DEFAULT_SIZE,
    width: int | None = None,
    height: int | None = None,
    algorithm_name: str = DEFAULT_ALGORITHM_NAME,
) -> bytes:
    """サムネイルPNGバイト列を生成して返す。"""
    img = create_thumbnail_image(
        title=title,
        draw_text=draw_text,
        text_position=text_position,
        font_scale=font_scale,
        size=size,
        width=width,
        height=height,
        algorithm_name=algorithm_name,
    )
    buffer = BytesIO()
    img.save(buffer, "PNG")
    return buffer.getvalue()


def save_thumbnail_png(
    output_path: str,
    title: str,
    draw_text: bool = False,
    text_position: str = DEFAULT_TEXT_POSITION,
    font_scale: float = DEFAULT_FONT_SCALE,
    size: int = DEFAULT_SIZE,
    width: int | None = None,
    height: int | None = None,
    algorithm_name: str = DEFAULT_ALGORITHM_NAME,
) -> str:
    """サムネイル画像をPNGで保存し、保存先パスを返す。"""
    img = create_thumbnail_image(
        title=title,
        draw_text=draw_text,
        text_position=text_position,
        font_scale=font_scale,
        size=size,
        width=width,
        height=height,
        algorithm_name=algorithm_name,
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG")
    return str(path)
