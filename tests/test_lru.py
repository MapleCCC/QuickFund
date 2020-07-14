from typing import List, TypeVar

from hypothesis import given
from hypothesis.strategies import integers, lists
from more_itertools import windowed

from fetcher.lru import LRU

# TODO we need to test on different element types.
# TODO we need to test on LRU after random sequence of update/evict operations.


@given(lists(integers()))
def test_len(l: List[int]) -> None:
    lru = LRU()
    for i in l:
        lru.update(i)
    assert len(lru) == len(set(l))


@given(integers())
def test_update_evict(i: int) -> None:
    lru = LRU()
    lru.update(i)
    assert i == lru.evict()


@given(lists(integers()))
def test_copy(l: List[int]) -> None:
    lru1 = LRU()
    for i in l:
        lru1.update(i)
    lru2 = lru1.copy()
    assert lru1 is not lru2
    assert len(lru1) == len(lru2)
    for _ in range(len(lru1)):
        assert lru1.evict() == lru2.evict()
    assert len(lru1) == len(lru2) == 0


T = TypeVar("T")


def rfind(l: List[T], elem: T) -> int:
    for i in range(len(l) - 1, -1, -1):
        if l[i] == elem:
            return i
    return -1


@given(lists(integers()))
def test_lru_order(l: List[int]) -> None:
    lru = LRU()
    for i in l:
        lru.update(i)
    evicted = []
    for _ in range(len(lru)):
        evicted.append(lru.evict())
    assert len(lru) == 0
    for e in evicted:
        assert e in l
    if len(evicted) >= 2:
        for p, n in windowed(evicted, 2):
            assert rfind(l, p) < rfind(l, n)
