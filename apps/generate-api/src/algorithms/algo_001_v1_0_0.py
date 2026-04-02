"""
001_v1.0.0 アルゴリズム実装
"""

import hashlib
import random
from colorsys import hsv_to_rgb

import numpy as np
from PIL import Image

SATURATION_MIN = 0.5
BRIGHTNESS_MIN = 0.6
WARP_LAYERS = 4
WARP_DISTORTION_BASE = 0.15
WARP_FEEDBACK_ITERATIONS = 2
NOISE_OCTAVES = 4
FINE_NOISE_STRENGTH = 0.15
CHANNEL_OCTAVES = 3
COLOR_WEIGHTS = np.array([6.0, 3.0, 1.0])
COLOR_CONTRIBUTION_RATIO = {
    "color": 0.4,
    "noise": 0.4,
    "field": 0.2,
}


def generate_001_v1_0_0(
    title: str,
    width: int,
    height: int,
) -> Image.Image:
    """001_v1.0.0: 現行のノイズ+ワープベース抽象パターン。"""
    hash_obj = hashlib.sha256(title.encode("utf-8"))
    hash_value = int(hash_obj.hexdigest(), 16)

    random.seed(hash_value % (2**31))
    np.random.seed(hash_value % (2**31))

    pattern = np.zeros((height, width, 3), dtype=np.uint8)

    hue_base = (hash_value % 360) / 360.0
    hue_offset1 = ((hash_value >> 8) % 91 + 30) / 360.0
    hue_offset2 = ((hash_value >> 12) % 91 + 30) / 360.0

    base_hues = [
        hue_base,
        (hue_base + hue_offset1) % 1.0,
        (hue_base + hue_offset2) % 1.0,
    ]

    saturation = SATURATION_MIN + ((hash_value >> 16) % 50) / 100.0
    brightness = BRIGHTNESS_MIN + ((hash_value >> 24) % 40) / 100.0

    colors_rgb = []
    for hue in base_hues:
        r, g, b = hsv_to_rgb(hue, saturation, brightness)
        colors_rgb.append((r, g, b))

    channel_colors = colors_rgb[0:3]

    x_coords = np.arange(width)
    y_coords = np.arange(height)
    xx, yy = np.meshgrid(x_coords, y_coords)

    max_dim = float(max(width, height))
    xx_norm = (xx - (width / 2.0)) / max_dim + 0.5
    yy_norm = (yy - (height / 2.0)) / max_dim + 0.5

    axis_rotation_angle = ((hash_value >> 32) % 360) * (np.pi / 180.0)
    axis_cos = np.cos(axis_rotation_angle)
    axis_sin = np.sin(axis_rotation_angle)
    xx_centered = xx_norm - 0.5
    yy_centered = yy_norm - 0.5
    xx_rot = xx_centered * axis_cos - yy_centered * axis_sin + 0.5
    yy_rot = xx_centered * axis_sin + yy_centered * axis_cos + 0.5

    warp_x = xx_rot.copy().astype(float)
    warp_y = yy_rot.copy().astype(float)

    for warp_layer in range(WARP_LAYERS):
        freq_scale = 2 ** (warp_layer + 1)
        phase_base = (hash_value >> (warp_layer * 8)) % 100 / 100.0

        distortion = WARP_DISTORTION_BASE / freq_scale
        warp_x += distortion * np.sin(
            2 * np.pi * freq_scale * warp_y + 2 * np.pi * phase_base
        )
        warp_x += distortion * np.cos(
            2 * np.pi * (freq_scale * 0.7) * warp_y**2 + 2 * np.pi * (phase_base + 0.3)
        )

        warp_y += distortion * np.cos(
            2 * np.pi * freq_scale * warp_x + 2 * np.pi * (phase_base + 0.5)
        )
        warp_y += distortion * np.sin(
            2 * np.pi * (freq_scale * 0.7) * warp_x**2 + 2 * np.pi * (phase_base + 0.1)
        )

    for _ in range(WARP_FEEDBACK_ITERATIONS):
        r_squared = (warp_x - 0.5) ** 2 + (warp_y - 0.5) ** 2
        rotation = 2 * np.pi * r_squared * ((hash_value >> 16) % 100) / 100.0
        cos_rot = np.cos(rotation)
        sin_rot = np.sin(rotation)

        warp_x_new = (warp_x - 0.5) * cos_rot - (warp_y - 0.5) * sin_rot + 0.5
        warp_y_new = (warp_x - 0.5) * sin_rot + (warp_y - 0.5) * cos_rot + 0.5

        warp_x = warp_x_new * 0.9 + warp_x * 0.1
        warp_y = warp_y_new * 0.9 + warp_y * 0.1

    field = np.zeros((height, width))
    for octave in range(NOISE_OCTAVES):
        base_freq = ((hash_value >> (octave * 6)) % 10) + 2
        octave_freq = base_freq * (octave + 1) * 0.7

        gradient_x = np.sin(octave * 1.3 + warp_x * octave_freq * 0.5) * np.cos(
            warp_y * octave_freq * 0.3
        )
        gradient_y = np.cos(octave * 0.9 + warp_y * octave_freq * 0.5) * np.sin(
            warp_x * octave_freq * 0.3
        )

        dot_product = gradient_x * warp_x + gradient_y * warp_y
        noise_octave = np.sin(dot_product * np.pi * octave_freq) * np.cos(
            dot_product * octave_freq * 0.5
        )

        weight = 0.5**octave
        field += noise_octave * weight

    np.random.seed(hash_value % (2**31))
    fine_noise = np.random.randn(height, width) * FINE_NOISE_STRENGTH
    field += fine_noise
    field = (field - field.min()) / (field.max() - field.min() + 1e-8)

    for c in range(3):
        channel_seed = (hash_value >> (c * 8)) % (2**31)
        np.random.seed(channel_seed)

        extra_warp_factor = 0.1 * (c + 1) / 3
        warp_x_c = warp_x + extra_warp_factor * np.sin(2 * np.pi * (c + 1) * warp_y)
        warp_y_c = warp_y + extra_warp_factor * np.cos(2 * np.pi * (c + 2) * warp_x)

        channel_field = np.zeros((height, width))
        for freq_octave in range(CHANNEL_OCTAVES):
            freq_var = ((channel_seed >> (freq_octave * 4)) % 7) + 1
            angle_field = np.arctan2(warp_y_c - 0.5, warp_x_c - 0.5)
            grad_angle = angle_field + freq_var * warp_x_c * warp_y_c

            grad_x = np.cos(grad_angle) * freq_var
            grad_y = np.sin(grad_angle) * freq_var

            dot = grad_x * warp_x_c + grad_y * warp_y_c
            noise_component = np.sin(dot * np.pi * freq_var) * np.cos(
                dot * freq_var * 0.7
            )
            channel_field += noise_component * (0.5**freq_octave)

        channel_field = (channel_field - channel_field.min()) / (
            channel_field.max() - channel_field.min() + 1e-8
        )

        weights = COLOR_WEIGHTS.copy() / COLOR_WEIGHTS.sum()
        combined = np.zeros((height, width))
        for color_idx in range(3):
            color_component = channel_colors[color_idx][c]
            color_contribution = (
                color_component * COLOR_CONTRIBUTION_RATIO["color"]
                + channel_field * COLOR_CONTRIBUTION_RATIO["noise"]
                + field * COLOR_CONTRIBUTION_RATIO["field"]
            )
            combined += color_contribution * weights[color_idx]

        pattern[:, :, c] = np.clip(combined * 255, 0, 255).astype(np.uint8)

    return Image.fromarray(pattern).convert("RGB")
