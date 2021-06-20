from collections.abc import Callable, Iterable, Iterator
from typing import Any, TypeVar


T = TypeVar("T")
S = TypeVar("S")


def tqdm(iterable: Iterable[T], *args: Any, **kwargs: Any) -> Iterator[T]:
    ...


def trange(n: int, *args: Any, **kwargs: Any) -> Iterator[int]:
    ...


def tmap(
    fn: Callable[[T], S], iterable: Iterable[T], *args: Any, **kwargs: Any
) -> Iterator[S]:
    ...


def tenumerate(
    iterable: Iterable[T], *args: Any, **kwargs: Any
) -> Iterator[tuple[int, T]]:
    ...


def thread_map(
    fn: Callable[[T], S], iterable: Iterable[T], *args: Any, **kwargs: Any
) -> Iterator[S]:
    ...
