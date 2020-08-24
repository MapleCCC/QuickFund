from typing import Any, List

from hypothesis import given
from hypothesis.strategies import from_type, lists
from more_itertools import windowed

from fetcher.lru import LRU

# TODO we need to test on LRU after random sequence of update/evict operations.


@given(lists(from_type(type)))
def test_size(l: List) -> None:
    lru = LRU()
    lru.batch_update(l)
    assert lru.size == len(set(l))


@given(from_type(type))
def test_update_evict(i: Any) -> None:
    lru = LRU()
    lru.update(i)
    assert i == lru.evict()


@given(lists(from_type(type)))
def test_copy(l: List) -> None:
    lru1 = LRU()
    lru1.batch_update(l)
    lru2 = lru1.copy()
    assert lru1 is not lru2
    assert lru1.size == lru2.size
    for _ in range(lru1.size):
        assert lru1.evict() == lru2.evict()
    assert lru1.size == lru2.size == 0


def rfind(l: List, elem: Any) -> int:
    for i in range(len(l) - 1, -1, -1):
        if l[i] == elem:
            return i
    return -1


@given(lists(from_type(type)))
def test_lru_order(l: List) -> None:
    lru = LRU()
    lru.batch_update(l)
    evicted = []
    for _ in range(lru.size):
        evicted.append(lru.evict())
    assert lru.size == 0
    for e in evicted:
        assert e in l
    if len(evicted) >= 2:
        for p, n in windowed(evicted, 2):
            assert rfind(l, p) < rfind(l, n)
