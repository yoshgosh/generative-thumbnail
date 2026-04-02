"""
画像生成アルゴリズム実装パッケージ
"""

from collections.abc import Callable

from .algo_001_v1_0_0 import generate_001_v1_0_0

DEFAULT_ALGORITHM_NAME = "001_v1.0.0"


def register_algorithms(
    register_algorithm: Callable[[str, Callable, str], None],
) -> None:
    """利用可能なアルゴリズムをまとめて登録する。"""
    register_algorithm(
        name=DEFAULT_ALGORITHM_NAME,
        generate=generate_001_v1_0_0,
        description="Current default abstract generator (noise + warp)",
    )
