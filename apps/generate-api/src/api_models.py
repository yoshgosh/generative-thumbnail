"""
HTTP API用のリクエストモデル
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.image_generator import DEFAULT_ALGORITHM_NAME
from src.thumbnail_service import DEFAULT_FONT_SCALE, DEFAULT_SIZE, DEFAULT_TEXT_POSITION


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1)
    text: bool = False
    text_position: Literal[
        "center",
        "top-left",
        "top-right",
        "bottom-left",
        "bottom-right",
        "c",
        "tl",
        "tr",
        "bl",
        "br",
    ] = DEFAULT_TEXT_POSITION
    font_scale: float = DEFAULT_FONT_SCALE
    size: int = DEFAULT_SIZE
    width: int | None = None
    height: int | None = None
    algorithm: str = DEFAULT_ALGORITHM_NAME
    save: bool = False
