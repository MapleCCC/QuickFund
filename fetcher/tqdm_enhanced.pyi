from typing import Any, Callable, Iterable, Iterator, Tuple, TypeVar


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
) -> Iterator[Tuple[int, T]]:
    ...


def thread_map(
    fn: Callable[[T], S], iterable: Iterable[T], *args: Any, **kwargs: Any
) -> Iterator[S]:
    ...
