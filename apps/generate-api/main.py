#!/usr/bin/env python3
"""
ジェネレーティブデザインによるサムネイル生成プログラム
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from src.image_generator import DEFAULT_ALGORITHM_NAME, list_algorithms
from src.thumbnail_service import (
    DEFAULT_TEXT_POSITION,
    DEFAULT_FONT_SCALE,
    DEFAULT_SIZE,
    save_thumbnail_png,
)

DEFAULT_OUTPUT_DIR = "output"


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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{title}.png"
    filepath = os.path.join(output_dir, filename)
    return save_thumbnail_png(
        output_path=filepath,
        title=title,
        draw_text=draw_text,
        text_position=text_position,
        font_scale=font_scale,
        size=size,
        width=width,
        height=height,
        algorithm_name=algorithm_name,
    )


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
