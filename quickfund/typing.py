import shelve
from collections.abc import Callable, KeysView, ValuesView
from typing import Generic, Optional, Protocol, TypeVar, Union, overload


__all__ = ["Shelf", "IdentityDecorator"]


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
FuncT = TypeVar("FuncT", bound=Callable)


# TODO the stdlib shelve.Shelf should become a generic type, so we don't
# need to use the following hack
class Shelf(shelve.Shelf, Generic[K, V]):
    def __getitem__(self, key: K) -> V:
        ...

    def __setitem__(self, key: K, value: V) -> None:
        ...

    def __delitem__(self, key: K) -> None:
        ...

    def __contains__(self, key: K) -> bool:
        ...

    @overload
    def get(self, key: K) -> Optional[V]:
        ...

    @overload
    def get(self, key: K, default: T) -> Union[V, T]:
        ...

    def keys(self) -> KeysView[K]:
        ...

    def values(self) -> ValuesView[K]:
        ...


class IdentityDecorator(Protocol):
    def __call__(self, __func: FuncT) -> FuncT:
        ...
