import shelve
from collections.abc import KeysView, ValuesView
from typing import Generic, Optional, TypeVar, Union, overload


__all__ = ["Shelf"]


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


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
