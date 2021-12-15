from collections.abc import Callable
from typing import Protocol, TypeVar

from typing_extensions import ParamSpec


__all__ = ["IdentityDecorator"]


P = ParamSpec("P")
R = TypeVar("R")


class IdentityDecorator(Protocol):
    def __call__(self, __func: Callable[P, R]) -> Callable[P, R]:
        ...
