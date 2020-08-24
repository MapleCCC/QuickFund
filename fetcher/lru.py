"""
TODO add introduction and elaborated algorithmic details.
"""

# postponed evaluation of type annotations. For type annotating LRU.copy()
# method.
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Type

# from collections import deque

# TODO elaborate on algorithmic analysis and time complexity of all operations
# TODO try other reconstruct criteria, like ratio of dummy cell count
# against total cell count, instead of absolute number of dummy cell count
# TODO elaborate on the algorithmic details. About how the data structure works under
# the hood.

__all__ = ["LRU"]


LRU_MAX_DUMMY_CELL_NUM = 200


def switch(iterable: Iterable) -> Iterator:
    """
    An itertools to switch two elements in every two-tuple yielded from the iterable.

    `iterable`: An iterable of two-tuple.
    """
    return ((y, x) for x, y in iterable)


class DummyCell:
    """ A singleton to signal lack of value """

    _singleton = None

    def __new__(cls: Type[DummyCell]) -> DummyCell:
        if cls._singleton is None:
            cls._singleton = object.__new__(cls)
        return cls._singleton

    def __str__(self) -> str:
        return "_DUMMY_CELL"

    __repr__ = __str__


# A singleton to signal lack of value
_DUMMY_CELL = DummyCell()


class LRU:
    """
    A data structure that realizes the LRU (Least-Recently Used) mechanism
    """

    def __init__(self) -> None:
        # TODO add `maxsize` argument
        self._storage: List = []
        self._indexer: Dict[Any, int] = {}
        self._dummy_cell_count: int = 0
        self._offset: int = 0

    __slots__ = ["_storage", "_indexer", "_dummy_cell_count", "_offset"]

    @property
    def size(self) -> int:
        """ Return the logical element number of the LRU container """

        # Note the invariant: len(indexer) + dummy_cell_count === len(storage)
        # Alternative: return len(self._indexer)
        return len(self._storage) - self._dummy_cell_count

    def empty(self) -> bool:
        """ Check if the LRU container is empty """
        return self.size == 0

    def copy(self) -> LRU:
        """ Return a deep copy of the LRU container """

        new_lru = LRU()
        new_lru._storage = self._storage.copy()
        new_lru._indexer = self._indexer.copy()
        new_lru._dummy_cell_count = self._dummy_cell_count
        new_lru._offset = self._offset
        return new_lru

    def __str__(self) -> str:
        """ Return a string representation of the LRU container """
        logical_content = [elm for elm in self._storage if elm is not _DUMMY_CELL]
        return f"LRU({logical_content})"

    def __repr__(self) -> str:
        """ Return a developer-oriented internal representation of the LRU container """
        return f"LRU({self._storage})"

    def update(self, elem: Any) -> None:
        """
        Update the recency of an element in a LRU container, i.e., promote the element to be most-recently used.
        """

        if elem in self._indexer:
            index = self._indexer[elem]
            # Alternative: self._storage[index] = self.__class__._DUMMY_CELL
            self._storage[index] = _DUMMY_CELL
            self._dummy_cell_count += 1
            self._storage.append(elem)
            self._indexer[elem] = len(self._storage) - 1
        else:
            self._storage.append(elem)
            self._indexer[elem] = len(self._storage) - 1

        if self._dummy_cell_count > LRU_MAX_DUMMY_CELL_NUM:
            self._reconstruct()

    def batch_update(self, elems: Iterable) -> None:
        """ Equivalent to a sequence of update() operations """

        for elem in elems:
            self.update(elem)

    def evict(self) -> Any:
        """ Remove and return the least-recently used element in the LRU container """

        if self.empty():
            raise KeyError("evict from empty LRU")

        oldest_non_dummy_cell_elem = None
        oldest_non_dummy_cell_index = None

        for i, elem in enumerate(self._storage[self._offset :], start=self._offset):
            if elem is not _DUMMY_CELL:
                oldest_non_dummy_cell_elem = elem
                oldest_non_dummy_cell_index = i
                break

        assert oldest_non_dummy_cell_index is not None

        self._storage[oldest_non_dummy_cell_index] = _DUMMY_CELL
        self._dummy_cell_count += 1
        self._offset = oldest_non_dummy_cell_index + 1
        del self._indexer[oldest_non_dummy_cell_elem]

        if self._dummy_cell_count > LRU_MAX_DUMMY_CELL_NUM:
            self._reconstruct()

        return oldest_non_dummy_cell_elem

    def _reconstruct(self) -> None:
        """
        An internal method to reconstruct the LRU container, to remove all dummy cells and compact the internal memory representation.
        """

        self._dummy_cell_count = 0
        self._offset = 0

        old_storage = self._storage
        self._storage = [elm for elm in old_storage if elm is not _DUMMY_CELL]

        self._indexer.update(switch(enumerate(self._storage)))


if __name__ == "__main__":
    l = LRU()
    l.update(1)
    l.update(2)
    l.update(3)
    l.update(4)
    l.evict()
    l.evict()
    l.evict()
    # Temporarily set LRU_MAX_DUMMY_CELL_NUM to 2, so as to test on
    # reconstruct logic.
