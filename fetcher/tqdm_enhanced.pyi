from typing import Any, Callable, Iterable, Iterator, Tuple, TypeVar, overload

_T = TypeVar("_T")
_S = TypeVar("_S")


@overload
def tqdm(iterable: Iterable[_T], *args: Any, **kwargs: Any) -> Iterator[_T]:
    ...


def tqdm(iterable: Iterable, *args: Any, **kwargs: Any) -> Iterator:
    ...


def trange(n: int, *args: Any, **kwargs: Any) -> Iterator[int]:
    ...


@overload
def tmap(
    fn: Callable[[_T], _S], iterable: Iterable[_T], *args: Any, **kwargs: Any
) -> Iterator[_S]:
    ...


def tmap(
    fn: Callable[..., _S], iterable: Iterable, *args: Any, **kwargs: Any
) -> Iterator[_S]:
    ...


@overload
def tenumerate(
    iterable: Iterable[_T], *args: Any, **kwargs: Any
) -> Iterator[Tuple[int, _T]]:
    ...


def tenumerate(
    iterable: Iterable, *args: Any, **kwargs: Any
) -> Iterator[Tuple[int, Any]]:
    ...


@overload
def thread_map(
    fn: Callable[[_T], _S], iterable: Iterable[_T], *args: Any, **kwargs: Any
) -> Iterator[_S]:
    ...


def thread_map(
    fn: Callable[..., _S], iterable: Iterable, *args: Any, **kwargs: Any
) -> Iterator[_S]:
    ...
