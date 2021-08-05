from collections.abc import Callable
from typing import Protocol, TypeVar


__all__ = ["IdentityDecorator"]


FuncT = TypeVar("FuncT", bound=Callable)


class IdentityDecorator(Protocol):
    def __call__(self, __func: FuncT) -> FuncT:
        ...
