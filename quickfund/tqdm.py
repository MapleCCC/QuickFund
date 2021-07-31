import contextlib
import os
from collections.abc import Iterable, Iterator
from typing import Awaitable, TypeVar

from colorama import Fore, Style
from tqdm.asyncio import tqdm_asyncio
from tqdm.contrib import tenumerate as std_tenumerate


__all__ = ["tenumerate", "tqdm_asyncio"]


T = TypeVar("T")


# Refer to https://github.com/tqdm/tqdm/issues/454
# FIXME: wait for the fix in upstream repository to land
if os.name == "nt":
    tqdm_config = {"ascii": True}


# FIXME tqdm supports a `colour` argument, there is no need for wrapping in bright green context?
# https://github.com/tartley/colorama/issues/217
# https://github.com/tartley/colorama/pull/222
@contextlib.contextmanager
def bright_green_context():
    # FIXME we will lose the previous style. There is no way to restore the style
    # before the call to our function. This is problematic in the situation when
    # nesting colored console contexts are present.
    print(Style.BRIGHT + Fore.GREEN, end="")
    yield
    print(Style.RESET_ALL, end="")


def tenumerate(
    iterable: Iterable[T], start: int = 0, *args, **kwargs
) -> Iterator[tuple[int, T]]:
    with bright_green_context():
        print()
        yield from std_tenumerate(iterable, start, *args, **kwargs, **tqdm_config)
        print()


std_gather = tqdm_asyncio.gather


# FIXME tqdm_asyncio.gather takes an iterable of Awaitable, while asyncio.gather
# takes every Awaitable as a single argument. Open a PR to fix the dismatch.
async def gather(aws: Iterable[Awaitable[T]], **kwargs) -> list[T]:
    with bright_green_context():
        print()
        res = await std_gather(aws, **kwargs, **tqdm_config)
        print()
        return res


# TODO open PR to add type annotation to tqdm_asyncio.gather
tqdm_asyncio.gather = gather  # type: ignore
