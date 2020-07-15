# postponed evaluation of type annotations. For type annotating LRU.copy()
# method.
from __future__ import annotations

import operator
from functools import partial
from itertools import filterfalse
from typing import Any, ClassVar, Dict, List

from more_itertools import replace

# from collections import deque

# TODO elaborate on algorithmic analysis and time complexity of all operations
# TODO try other reconstruct criteria, like ratio of dummy cell count
# against total cell count, instead of absolute number of dummy cell count

__all__ = ["LRU"]


LRU_MAX_DUMMY_CELL_NUM = 200


class LRU:
    _DUMMY_CELL: ClassVar[object] = object()

    def __init__(self) -> None:
        self._storage: List = []
        self._indexer: Dict[Any, int] = {}
        self._dummy_cell_count: int = 0
        self._offset: int = 0

    __slots__ = ["_storage", "_indexer", "_dummy_cell_count", "_offset"]

    def __len__(self) -> int:
        # Note the invariant: len(indexer) + dummy_cell_count === len(storage)
        # return len(self._indexer)
        return len(self._storage) - self._dummy_cell_count

    def copy(self) -> LRU:
        new_lru = LRU()
        new_lru._storage = self._storage.copy()
        new_lru._indexer = self._indexer.copy()
        new_lru._dummy_cell_count = self._dummy_cell_count
        new_lru._offset = self._offset
        return new_lru

    def __str__(self) -> str:
        filterfunc = partial(operator.is_not, LRU._DUMMY_CELL)
        logical_content = list(filterfalse(filterfunc, self._storage))
        return f"LRU({logical_content})"

    def __repr__(self) -> str:
        filterfunc = partial(operator.is_not, LRU._DUMMY_CELL)
        repr_content = list(replace(self._storage, filterfunc, ["_DUMMY_CELL"]))
        return f"LRU({repr_content})"

    # TODO god damn it, we don't need this. What's wrong with you? Are
    # you too sleepy that you become insane?
    @classmethod
    def empty_lru(cls) -> LRU:
        return cls()

    def update(self, elem: Any) -> None:
        if elem in self._indexer:
            index = self._indexer[elem]
            # self._storage[index] = self.__class__._DUMMY_CELL
            self._storage[index] = LRU._DUMMY_CELL
            self._dummy_cell_count += 1
            self._storage.append(elem)
            self._indexer[elem] = len(self._storage) - 1
        else:
            self._storage.append(elem)
            self._indexer[elem] = len(self._storage) - 1

        if self._dummy_cell_count > LRU_MAX_DUMMY_CELL_NUM:
            self._reconstruct()

    def evict(self) -> Any:
        if self._dummy_cell_count == len(self._storage):
            raise KeyError("evict from empty LRU")

        oldest_non_dummy_cell_elem = None
        oldest_non_dummy_cell_index = 0

        for i, elem in enumerate(self._storage[self._offset :], start=self._offset):
            if elem is not LRU._DUMMY_CELL:
                oldest_non_dummy_cell_elem = elem
                oldest_non_dummy_cell_index = i
                break

        self._storage[oldest_non_dummy_cell_index] = LRU._DUMMY_CELL
        self._dummy_cell_count += 1
        self._offset = oldest_non_dummy_cell_index + 1
        del self._indexer[oldest_non_dummy_cell_elem]

        if self._dummy_cell_count > LRU_MAX_DUMMY_CELL_NUM:
            self._reconstruct()

        return oldest_non_dummy_cell_elem

    def _reconstruct(self) -> None:
        self._dummy_cell_count = 0
        self._offset = 0
        old_storage = self._storage
        self._storage = []

        for elem in old_storage:
            if elem is not LRU._DUMMY_CELL:
                self._storage.append(elem)
                self._indexer[elem] = len(self._storage) - 1


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
