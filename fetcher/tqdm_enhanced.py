import functools
import os
from collections.abc import Callable, Iterable, Iterator
from functools import partial
from typing import Any

from colorama import Fore, Style
from tqdm import tqdm as std_tqdm
from tqdm import trange as std_trange
from tqdm.contrib import tenumerate as std_tenumerate
from tqdm.contrib import tmap as std_tmap
from tqdm.contrib.concurrent import thread_map as std_thread_map


__all__ = ["tqdm", "trange", "tmap", "tenumerate", "thread_map"]


# Refer to https://github.com/tqdm/tqdm/issues/454
# FIXME: wait for the fix in upstream repository to land
if os.name == "nt":
    std_tqdm = partial(std_tqdm, ascii=True)
    std_trange = partial(std_trange, ascii=True)
    std_tmap = partial(std_tmap, ascii=True)
    std_tenumerate = partial(std_tenumerate, ascii=True)
    std_thread_map = partial(std_thread_map, ascii=True)


def green_fore_color_console_wrapper(
    fn: Callable[..., Iterable]
) -> Callable[..., Iterator]:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Iterator:
        # FIXME we will lose the previous style. There is no way to restore the style
        # before the call to our function. This is problematic in the situation when
        # nesting colored console contexts are present.
        print()
        print(Style.BRIGHT + Fore.GREEN, end="")
        yield from iter(fn(*args, **kwargs))
        print(Style.RESET_ALL, end="")
        print()

    return wrapper


tqdm = green_fore_color_console_wrapper(std_tqdm)
trange = green_fore_color_console_wrapper(std_trange)
tmap = green_fore_color_console_wrapper(std_tmap)
tenumerate = green_fore_color_console_wrapper(std_tenumerate)
thread_map = green_fore_color_console_wrapper(std_thread_map)
