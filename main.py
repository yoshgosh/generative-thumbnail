#!/usr/bin/env python3
"""
ジェネレーティブデザインによるサムネイル生成プログラム
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from src.image_generator import (
    DEFAULT_ALGORITHM_NAME,
    generate_image,
    list_algorithms,
)
from src.text_renderer import draw_title_text

DEFAULT_SIZE = 500
DEFAULT_OUTPUT_DIR = "output"
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


def generate_thumbnail(
    title: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    draw_text: bool = False,
    text_position: str = DEFAULT_TEXT_POSITION,
    font_scale: float = DEFAULT_FONT_SCALE,
    size: int = DEFAULT_SIZE,
    width: int | None = None,
    height: int | None = None,
    algorithm_name: str = DEFAULT_ALGORITHM_NAME,
) -> str:
    """
    タイトルからサムネイル画像を生成する。

    Returns:
        生成された画像ファイルパス
    """
    Path(output_dir).mkdir(exist_ok=True)
    resolved_width, resolved_height = resolve_dimensions(
        size=size,
        width=width,
        height=height,
    )

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
            text_position=text_position,
            font_scale=font_scale,
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{title}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath, "PNG")
    return filepath


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


def main() -> None:
    algorithm_names = [spec.name for spec in list_algorithms()]

    parser = argparse.ArgumentParser(
        description="タイトルからサムネイル画像を生成する",
        add_help=False,
    )
    parser.add_argument("--help", action="help", help="ヘルプメッセージを表示して終了")
    parser.add_argument("title", help="画像生成のベースとなるタイトル")
    parser.add_argument("-t", "--text", action="store_true", help="画像にタイトルテキストを描画")
    parser.add_argument(
        "-tp",
        "--text-position",
        default="center",
        choices=[
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
        ],
        help="テキストの配置位置（デフォルト: center, tl/tr/bl/br/c も使用可）",
    )
    parser.add_argument(
        "-fs",
        "--font-scale",
        type=float,
        default=DEFAULT_FONT_SCALE,
        help=f"テキスト描画時のフォントサイズ比率（デフォルト: {DEFAULT_FONT_SCALE}）",
    )
    parser.add_argument(
        "-s",
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help=f"生成する画像のピクセルサイズ（横幅=高さ、デフォルト: {DEFAULT_SIZE}）",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=None,
        help="生成する画像の横幅（指定時は --size より優先）",
    )
    parser.add_argument(
        "-h",
        "--height",
        type=int,
        default=None,
        help="生成する画像の縦幅（指定時は --size より優先）",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"出力先ディレクトリ（デフォルト: {DEFAULT_OUTPUT_DIR}）",
    )
    parser.add_argument(
        "-a",
        "--algorithm",
        default=DEFAULT_ALGORITHM_NAME,
        choices=algorithm_names,
        help=f"使用する画像生成アルゴリズム（デフォルト: {DEFAULT_ALGORITHM_NAME}）",
    )

    args = parser.parse_args()
    tp = args.text_position.lower()
    args.text_position = TEXT_POSITION_MAP.get(tp, tp)

    try:
        filepath = generate_thumbnail(
            args.title,
            args.output,
            draw_text=args.text,
            text_position=args.text_position,
            font_scale=args.font_scale,
            size=args.size,
            width=args.width,
            height=args.height,
            algorithm_name=args.algorithm,
        )
        print("✓ サムネイル画像を生成しました")
        print(f"  タイトル: {args.title}")
        print(f"  アルゴリズム: {args.algorithm}")
        print(f"  保存先: {filepath}")
    except Exception as e:
        print(f"✗ エラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
