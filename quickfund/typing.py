import shelve
from collections.abc import KeysView, ValuesView
from typing import Generic, TypeVar


__all__ = ["Shelf"]


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

    def get(self, key: K, default: V = None) -> V:
        ...

    def keys(self) -> KeysView[K]:
        ...

    def values(self) -> ValuesView[K]:
        ...
