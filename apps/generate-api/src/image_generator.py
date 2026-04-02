"""
サムネイルのベース画像（抽象パターン）生成ロジック
"""

from dataclasses import dataclass
from typing import Callable

from PIL import Image

from .algorithms import DEFAULT_ALGORITHM_NAME, register_algorithms

ImageGeneratorFn = Callable[[str, int, int], Image.Image]


@dataclass(frozen=True)
class AlgorithmSpec:
    name: str
    generate: ImageGeneratorFn
    description: str = ""


_ALGORITHM_REGISTRY: dict[str, AlgorithmSpec] = {}


def register_algorithm(
    name: str,
    generate: ImageGeneratorFn,
    description: str = "",
) -> None:
    """画像生成アルゴリズムをレジストリへ登録する。"""
    _ALGORITHM_REGISTRY[name] = AlgorithmSpec(
        name=name,
        generate=generate,
        description=description,
    )


def get_algorithm(name: str) -> AlgorithmSpec:
    """アルゴリズム名から仕様を取得する。"""
    try:
        return _ALGORITHM_REGISTRY[name]
    except KeyError as exc:
        available = ", ".join(sorted(_ALGORITHM_REGISTRY.keys()))
        raise ValueError(
            f"Unknown algorithm: {name}. available: [{available}]"
        ) from exc


def list_algorithms() -> list[AlgorithmSpec]:
    """登録済みアルゴリズム一覧を返す。"""
    return [spec for _, spec in sorted(_ALGORITHM_REGISTRY.items(), key=lambda kv: kv[0])]


def generate_image(
    title: str,
    width: int,
    height: int,
    algorithm_name: str | None = None,
) -> Image.Image:
    """
    抽象パターン画像を生成する。

    algorithm_name 未指定時は DEFAULT_ALGORITHM_NAME を使用する。
    """
    resolved_algorithm_name = algorithm_name or DEFAULT_ALGORITHM_NAME
    spec = get_algorithm(resolved_algorithm_name)
    return spec.generate(title, width, height)


register_algorithms(register_algorithm)
