# from collections import deque
from typing import TypeVar, List, Dict

__all__ = ["LRU"]

T = TypeVar("T")

LRU_MAX_DUMMY_CELL_NUM = 200


class LRU:
    _DUMMY_CELL = object()

    def __init__(self) -> None:
        self._storage: List[T] = []
        self._indexer: Dict[T, int] = {}
        self._dummy_cell_count: int = 0
        self._offset: int = 0

    __slots__ = ["_storage", "_indexer", "_dummy_cell_count", "_offset"]

    def __len__(self) -> int:
        return len(self._storage)

    def update(self, elem: T) -> None:
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
            self.reconstruct()

    def evict(self) -> T:
        if self._dummy_cell_count == len(self._storage):
            raise KeyError("evict from empty LRU")

        oldest_non_dummy_cell_elem = None
        oldest_non_dummy_cell_index = 0

        for i, elem in enumerate(self._storage[self._offset :], start=self._offset):
            if elem != LRU._DUMMY_CELL:
                oldest_non_dummy_cell_elem = elem
                oldest_non_dummy_cell_index = i
                break

        self._storage[oldest_non_dummy_cell_index] = LRU._DUMMY_CELL
        self._dummy_cell_count += 1
        self._offset = oldest_non_dummy_cell_index + 1
        del self._indexer[oldest_non_dummy_cell_elem]

        if self._dummy_cell_count > LRU_MAX_DUMMY_CELL_NUM:
            self.reconstruct()

        return oldest_non_dummy_cell_elem

    def reconstruct(self) -> None:
        self._dummy_cell_count = 0
        self._offset = 0
        old_storage = self._storage
        self._storage = []

        for elem in old_storage:
            if elem != LRU._DUMMY_CELL:
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
    # Temporarily set LRU_MAX_DUMMY_CELL_NUM to 2, so as to test on reconstruct logic.
