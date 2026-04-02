"""
画像へのテキスト描画ロジック
"""

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_SIZE_MIN = 6
PADDING_TEXT = 20
DEFAULT_FONT_PATH = (
    Path(__file__).resolve().parent / "assets" / "fonts" / "NotoSansJP-Bold.ttf"
)


@lru_cache(maxsize=32)
def _load_font(font_size: int) -> ImageFont.ImageFont:
    if not DEFAULT_FONT_PATH.exists():
        raise FileNotFoundError(
            f"Bundled font not found: {DEFAULT_FONT_PATH}. "
            "Run `./scripts/install_font.sh` to install it."
        )
    return ImageFont.truetype(str(DEFAULT_FONT_PATH), font_size)


def draw_title_text(
    img: Image.Image,
    title: str,
    text_position: str = "center",
    font_scale: float = 0.05,
) -> Image.Image:
    """画像にタイトル文字を描画して返す。"""
    draw = ImageDraw.Draw(img)
    width, height = img.size
    font_size = max(FONT_SIZE_MIN, int(min(width, height) * font_scale))
    font = _load_font(font_size)

    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    padding = PADDING_TEXT

    if text_position == "center":
        x = (width - text_width) // 2 - bbox[0]
        y = (height - text_height) // 2 - bbox[1]
    elif text_position == "top-left":
        x = padding - bbox[0]
        y = padding - bbox[1]
    elif text_position == "top-right":
        x = width - text_width - padding - bbox[0]
        y = padding - bbox[1]
    elif text_position == "bottom-left":
        x = padding - bbox[0]
        y = height - text_height - padding - bbox[1]
    elif text_position == "bottom-right":
        x = width - text_width - padding - bbox[0]
        y = height - text_height - padding - bbox[1]
    else:
        x = (width - text_width) // 2 - bbox[0]
        y = (height - text_height) // 2 - bbox[1]

    draw.text((x, y), title, fill=(255, 255, 255), font=font)
    return img
