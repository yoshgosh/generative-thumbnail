#!/usr/bin/env python3
"""
ジェネレーティブデザインによるサムネイル生成プログラム
入力されたタイトルのハッシュ値を基に、抽象的なサムネイル画像を生成する
"""

import sys
import os
import argparse
import hashlib
import random
from datetime import datetime
from pathlib import Path
from colorsys import hsv_to_rgb
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ============================================================================
# 定数定義
# ============================================================================

# 画像生成のデフォルト値
DEFAULT_SIZE = 500
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_FONT_SCALE = 0.05 # 1/20
DEFAULT_TEXT_POSITION = "center"
MIN_SIZE = 16

# テキスト描画の設定
FONT_SIZE_MIN = 6
PADDING_TEXT = 20

# 色の生成パラメータ
SATURATION_MIN = 0.5
SATURATION_RANGE = 0.5
BRIGHTNESS_MIN = 0.6
BRIGHTNESS_RANGE = 0.4

# 座標歪みのパラメータ
WARP_LAYERS = 4
WARP_DISTORTION_BASE = 0.15
WARP_FEEDBACK_ITERATIONS = 2

# ノイズ生成のパラメータ
NOISE_OCTAVES = 4
FINE_NOISE_STRENGTH = 0.15
CHANNEL_OCTAVES = 3

# 色の出現割合 (6:3:1)
COLOR_WEIGHTS = np.array([6.0, 3.0, 1.0])

# 色成分の合成比率
COLOR_CONTRIBUTION_RATIO = {
    "color": 0.4,
    "noise": 0.4,
    "field": 0.2,
}

# フォントパス（優先順位順）
FONT_PATHS = [
    "/Library/Fonts/Noto Sans JP/static/NotoSansJP-Bold.ttf",
    "/System/Library/Fonts/NotoSansJP-Bold.otf",
    "/Library/Fonts/NotoSansJP-Bold.otf",
    "/usr/local/share/fonts/NotoSansJP-Bold.otf",
    "/System/Library/Fonts/Helvetica.ttc",
]

# テキスト位置の短縮形マッピング
TEXT_POSITION_MAP = {
    "c": "center",
    "tl": "top-left",
    "tr": "top-right",
    "bl": "bottom-left",
    "br": "bottom-right",
}

# ============================================================================


def generate_thumbnail(
    title: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    draw_text: bool = False,
    text_position: str = DEFAULT_TEXT_POSITION,
    font_scale: float = DEFAULT_FONT_SCALE,
    size: int = DEFAULT_SIZE,
    width: int | None = None,
    height: int | None = None,
) -> str:
    """
    タイトルからサムネイル画像を生成する

    Args:
        title: 画像生成のベースとなるタイトル文字列
        output_dir: 出力先ディレクトリ
        draw_text: Trueの場合、画像にタイトルテキストを描画
        text_position: テキストの配置位置（center, top-left, top-right, bottom-left, bottom-right）
        font_scale: テキストフォントサイズを画像サイズの何倍にするか（例: 0.0625 は 1/16）

    Returns:
        生成された画像ファイルのパス
    """
    # 出力ディレクトリの作成
    Path(output_dir).mkdir(exist_ok=True)

    # タイトルのハッシュ値を生成
    hash_obj = hashlib.sha256(title.encode("utf-8"))
    hash_value = int(hash_obj.hexdigest(), 16)

    # ランダムシード設定（ハッシュ値ベース）
    random.seed(hash_value % (2**31))
    np.random.seed(hash_value % (2**31))

    # 画像サイズ（デフォルトは size x size、width/height があれば優先）
    base_size = max(MIN_SIZE, int(size))
    width = max(MIN_SIZE, int(width if width is not None else base_size))
    height = max(MIN_SIZE, int(height if height is not None else base_size))

    # ベースパターンを生成（複雑かつ多元的な傾斜関数を使用）
    pattern = np.zeros((height, width, 3), dtype=np.uint8)

    # より豊かで意的なカラーパレットを生成
    # HSV色空間を使用して色相、彩度、明度をコントロール
    from colorsys import hsv_to_rgb

    # 色相を生成（0-360度の領域を選択）
    hue_base = (hash_value % 360) / 360.0

    # オフセットを可変に生成（30-120°の範囲で）
    hue_offset1 = ((hash_value >> 8) % 91 + 30) / 360.0  # 30-120°のランダムオフセット
    hue_offset2 = ((hash_value >> 12) % 91 + 30) / 360.0  # 別のランダムオフセット

    # 複数の主要色を生成（3色、可変オフセットで配置）
    base_hues = [
        hue_base,
        (hue_base + hue_offset1) % 1.0,
        (hue_base + hue_offset2) % 1.0,
    ]

    # トーンの多様性を加える（パステル調～濃い色など）
    saturation = (
        SATURATION_MIN + ((hash_value >> 16) % 50) / 100.0
    )  # 彩度：0.5～1.0（中～高彩度、より鮮やか）
    brightness = (
        BRIGHTNESS_MIN + ((hash_value >> 24) % 40) / 100.0
    )  # 明度：0.6～1.0（中明～明るい）

    # RGB値に変換
    colors_rgb = []
    for hue in base_hues:
        r, g, b = hsv_to_rgb(hue, saturation, brightness)
        colors_rgb.append((r, g, b))  # 0-1の浮動小数点のまま保持

    # RGB値を正規化された0-1範囲で複数用意（チャンネルごと）
    channel_colors = colors_rgb[0:3]  # RGB用に3色確保、足りなければループする

    # 複雑な傾斜関数のパラメータを生成
    freq_params = [((hash_value >> (i * 8)) % 8) + 1 for i in range(6)]
    phase_params = [((hash_value >> (16 + i * 6)) % 100) / 100.0 for i in range(6)]

    # 座標網を作成
    x_coords = np.arange(width)
    y_coords = np.arange(height)
    xx, yy = np.meshgrid(x_coords, y_coords)

    # 座標を等方化して正規化 [0, 1]
    # 長辺基準で正規化することで、長方形でもパターンの引き伸ばしを防ぐ
    max_dim = float(max(width, height))
    xx_norm = (xx - (width / 2.0)) / max_dim + 0.5
    yy_norm = (yy - (height / 2.0)) / max_dim + 0.5

    # 座標軸を中心基準で回転（タイトルから一意に決定）
    axis_rotation_angle = ((hash_value >> 32) % 360) * (np.pi / 180.0)
    axis_cos = np.cos(axis_rotation_angle)
    axis_sin = np.sin(axis_rotation_angle)
    xx_centered = xx_norm - 0.5
    yy_centered = yy_norm - 0.5
    xx_rot = xx_centered * axis_cos - yy_centered * axis_sin + 0.5
    yy_rot = xx_centered * axis_sin + yy_centered * axis_cos + 0.5

    # 複数層の非線形座標歪み（周期性を完全に破壊）
    # 第1層：sin波による歪み
    warp_x = xx_rot.copy().astype(float)
    warp_y = yy_rot.copy().astype(float)

    # 複数の周波数で座標を順序立てて歪める
    for warp_layer in range(WARP_LAYERS):
        freq_scale = 2 ** (warp_layer + 1)
        phase_base = (hash_value >> (warp_layer * 8)) % 100 / 100.0

        # X座標を歪める（Y依存）
        distortion = WARP_DISTORTION_BASE / freq_scale
        warp_x += distortion * np.sin(
            2 * np.pi * freq_scale * warp_y + 2 * np.pi * phase_base
        )
        warp_x += distortion * np.cos(
            2 * np.pi * (freq_scale * 0.7) * warp_y**2 + 2 * np.pi * (phase_base + 0.3)
        )

        # Y座標を歪める（X依存）
        warp_y += distortion * np.cos(
            2 * np.pi * freq_scale * warp_x + 2 * np.pi * (phase_base + 0.5)
        )
        warp_y += distortion * np.sin(
            2 * np.pi * (freq_scale * 0.7) * warp_x**2 + 2 * np.pi * (phase_base + 0.1)
        )

    # 循環的な歪み（非線形フィードバック）
    for _ in range(WARP_FEEDBACK_ITERATIONS):
        r_squared = (warp_x - 0.5) ** 2 + (warp_y - 0.5) ** 2
        rotation = 2 * np.pi * r_squared * ((hash_value >> 16) % 100) / 100.0
        cos_rot = np.cos(rotation)
        sin_rot = np.sin(rotation)

        warp_x_new = (warp_x - 0.5) * cos_rot - (warp_y - 0.5) * sin_rot + 0.5
        warp_y_new = (warp_x - 0.5) * sin_rot + (warp_y - 0.5) * cos_rot + 0.5

        warp_x = warp_x_new * 0.9 + warp_x * 0.1
        warp_y = warp_y_new * 0.9 + warp_y * 0.1

    # 歪んだ座標でノイズを生成
    field = np.zeros((height, width))

    # Perlin風のグラデーションノイズを模擬
    # ハッシュベースのランダムグラディエント
    for octave in range(NOISE_OCTAVES):
        # 周期を変動させる（このタイムステップの周期を変える）
        base_freq = ((hash_value >> (octave * 6)) % 10) + 2
        octave_freq = base_freq * (octave + 1) * 0.7

        # グラデーションの方向をランダムに生成（周期的でなく変動）
        gradient_x = np.sin(octave * 1.3 + warp_x * octave_freq * 0.5) * np.cos(
            warp_y * octave_freq * 0.3
        )
        gradient_y = np.cos(octave * 0.9 + warp_y * octave_freq * 0.5) * np.sin(
            warp_x * octave_freq * 0.3
        )

        # グラデーション関数を適用
        dot_product = gradient_x * warp_x + gradient_y * warp_y
        noise_octave = np.sin(dot_product * np.pi * octave_freq) * np.cos(
            dot_product * octave_freq * 0.5
        )

        weight = 0.5**octave
        field += noise_octave * weight

    # ランダムシードベースの高周波成分
    np.random.seed(hash_value % (2**31))
    fine_noise = np.random.randn(height, width) * FINE_NOISE_STRENGTH
    field += fine_noise

    # 値を [0, 1] の範囲に正規化
    field = (field - field.min()) / (field.max() - field.min() + 1e-8)

    # グラデーション基盤と組み合わせる
    # 各チャンネルに異なる色を使ってカラフルに（出現割合 6:3:1）
    for c in range(3):
        # チャンネル固有の歪んだ座標
        channel_seed = (hash_value >> (c * 8)) % (2**31)
        np.random.seed(channel_seed)

        # チャンネル固有の追加歪み
        extra_warp_factor = 0.1 * (c + 1) / 3
        warp_x_c = warp_x + extra_warp_factor * np.sin(2 * np.pi * (c + 1) * warp_y)
        warp_y_c = warp_y + extra_warp_factor * np.cos(2 * np.pi * (c + 2) * warp_x)

        # チャンネル固有のノイズパターン
        channel_field = np.zeros((height, width))

        # ランダムグラディエントをチャンネルごとに異なるスケールで
        for freq_octave in range(CHANNEL_OCTAVES):
            freq_var = ((channel_seed >> (freq_octave * 4)) % 7) + 1

            # 周期性を破壊：グラデーション角度を空間的に変化させる
            angle_field = np.arctan2(warp_y_c - 0.5, warp_x_c - 0.5)
            grad_angle = angle_field + freq_var * warp_x_c * warp_y_c

            # グラデーション成分
            grad_x = np.cos(grad_angle) * freq_var
            grad_y = np.sin(grad_angle) * freq_var

            # ドット積でノイズを生成
            dot = grad_x * warp_x_c + grad_y * warp_y_c
            noise_component = np.sin(dot * np.pi * freq_var) * np.cos(
                dot * freq_var * 0.7
            )

            channel_field += noise_component * (0.5**freq_octave)

        # 正規化
        channel_field = (channel_field - channel_field.min()) / (
            channel_field.max() - channel_field.min() + 1e-8
        )

        # 3色のそれぞれに対して計算（出現割合 weights: 6, 3, 1）
        weights = COLOR_WEIGHTS.copy() / COLOR_WEIGHTS.sum()  # 正規化して確率分布に

        # 3色の加重合成
        combined = np.zeros((height, width))
        for color_idx in range(3):
            color_component = channel_colors[color_idx][c]  # 各色のc番目チャンネル値
            color_contribution = (
                color_component * COLOR_CONTRIBUTION_RATIO["color"]  # 色相ベース
                + channel_field * COLOR_CONTRIBUTION_RATIO["noise"]  # ノイズパターン
                + field * COLOR_CONTRIBUTION_RATIO["field"]
            )  # グローバルフィールド
            combined += color_contribution * weights[color_idx]

        pattern[:, :, c] = np.clip(combined * 255, 0, 255).astype(np.uint8)

    # ファイル名生成（yyyyMMdd_HHMMSS_タイトル.png）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{title}.png"

    # 画像に変換
    img = Image.fromarray(pattern)
    filepath = os.path.join(output_dir, filename)

    # 画像を保存（RGB変換）
    img = img.convert("RGB")

    # テキスト描画オプション
    if draw_text:
        # テキストを描画
        draw = ImageDraw.Draw(img)

        # フォント設定（デフォルトは画像の1/20）
        font_size = max(FONT_SIZE_MIN, int(min(width, height) * font_scale))

        # Noto Sans JPボールドの場所を探す
        font_paths = FONT_PATHS

        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except Exception:
                    continue

        # フォントが見つからない場合はデフォルトフォント
        if font is None:
            # 最後の手段：システムフォント
            try:
                font = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica.ttc", font_size
                )
            except Exception:
                font = ImageFont.load_default()

        # テキスト配置：位置に応じた計算
        text = title
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # パディング（四隅の場合）
        padding = PADDING_TEXT

        # 位置に応じてx, yを計算
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
            # デフォルト：中央
            x = (width - text_width) // 2 - bbox[0]
            y = (height - text_height) // 2 - bbox[1]

        # 白いテキストを描画
        draw.text((x, y), text, fill=(255, 255, 255), font=font)

    img.save(filepath, "PNG")

    return filepath


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="タイトルからサムネイル画像を生成する",
        add_help=False,
    )
    parser.add_argument(
        "--help",
        action="help",
        help="ヘルプメッセージを表示して終了",
    )
    parser.add_argument("title", help="画像生成のベースとなるタイトル")
    parser.add_argument(
        "-t",
        "--text",
        action="store_true",
        help="画像にタイトルテキストを描画",
    )
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
        help=f"テキストを描画する場合のフォントサイズの割合（画像サイズに対する比率、デフォルト {DEFAULT_FONT_SCALE}）",
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

    args = parser.parse_args()

    # テキスト位置の略称を正規化
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
        )
        print(f"✓ サムネイル画像を生成しました")
        print(f"  タイトル: {args.title}")
        print(f"  保存先: {filepath}")
    except Exception as e:
        print(f"✗ エラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
