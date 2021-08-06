from __future__ import annotations

import asyncio
import atexit
import functools
import inspect
import locale
import sys
import time
import traceback
from collections.abc import Awaitable, Callable
from types import MethodType
from typing import IO, TypeVar

import aiohttp
import click
import regex
from colorama import Fore, Style
from typing_extensions import ParamSpec

from .typing import IdentityDecorator


__all__ = [
    "bright_red",
    "bright_green",
    "bright_blue",
    "print_traceback_digest",
    "Logger",
    "timefunc",
    "on_failure_raises",
    "pause_at_exit",
    "schedule_at_loop_close",
    "graceful_shutdown_client_session",
    "get_running_client_session",
]


P = ParamSpec("P")
R = TypeVar("R")


def bright_red(s: str) -> str:
    """
    Augment a string, so that when printed to console, the string is displayed in bright red color.
    """
    return Style.BRIGHT + Fore.RED + s + Style.RESET_ALL


def bright_green(s: str) -> str:
    """
    Augment a string, so that when printed to console, the string is displayed in bright green color.
    """
    return Style.BRIGHT + Fore.GREEN + s + Style.RESET_ALL


def bright_blue(s: str) -> str:
    """
    Augment a string, so that when printed to console, the string is displayed in bright blue color.
    """
    return Style.BRIGHT + Fore.BLUE + s + Style.RESET_ALL


def split_paragraphs(text: str) -> list[str]:
    """
    Similar to splitlines(), except it splits paragraphs, not lines.
    """
    return regex.split(r"\n{2,}", text)


def retrieve_succinct_traceback() -> str:
    """
    A utility that retrive succint traceback digest from a complete traceback string.
    """

    tb = traceback.format_exc()
    return "\n".join(pg.splitlines()[-1] for pg in split_paragraphs(tb))


localization_table = {
    "zh_CN": {
        "During handling of the above exception, another exception occurred:": "在处理以上所述的错误时，发生了如下的另一个错误:",
        "The above exception was the direct cause of the following exception:": "以上所述的错误直接引发了以下错误:",
        "PermissionError": "权限错误",
        "RuntimeError": "运行时错误",
        "KeyboardInterrupt": "来自键盘的中断信号",
        "Server Error": "服务器错误",
    }
}


local_lang = locale.getdefaultlocale()[0]
if not local_lang or local_lang not in localization_table:
    # If we can't detect local langauge or we don't have translation
    # dictionary for the given local language, we can either
    # 1. raise an exception, or
    # 2. fall back to English.
    local_lang = "en_US"

if local_lang.startswith("en"):
    # English is the default language of CPython, so we don't need
    # to do anything additionally.
    translation_dict = {}
else:
    translation_dict = localization_table[local_lang]


def localize(s: str) -> str:
    """
    Localize a string with a pre-defined translation dictionary.

    If we can't detect local langauge or we don't have translation dictionary for the
        given local language, we simply fall back to English.
    """

    # FIXME what if some translation rules conflict with each other?
    # i.e., how to handle the situation when the order of applying
    # translation rules matters?
    for src, dst in translation_dict.items():
        s = s.replace(src, dst)

    return s


def print_traceback_digest(
    colored: bool = True,
    numbered: bool = True,
    indented: bool = True,
    localized: bool = True,
) -> None:
    """
    Print a digest of traceback

    `colored`: A flag to control whether should print with color.
    `numbered`: A flag to control whether should print with line number prepended.
    `indented`: A flag to control whether should print with additional indentation, to emphasize.
    `localized`: A flag to control whether should localize the traceback digest.
    """

    digest = retrieve_succinct_traceback()

    if localized:
        digest = localize(digest)

    if colored:
        digest = bright_red(digest)

    lines = digest.splitlines()

    for i, line in enumerate(lines):

        if numbered and len(lines) > 1:
            lineno = i + 1
            lines[i] = str(lineno) + ". " + line

        if indented:
            lines[i] = "    " + line

    digest = "\n".join(lines)

    print(digest)


def no_op(*_, **__) -> None:
    pass


class Logger:
    """
    A lightweight logger.

    It's just a thin wrapper over the builtin print function, except that it prints
    strings with order numbers prepended.
    """

    def __init__(self) -> None:
        self._index = 1

    def log(self, s: str, file: IO = sys.stdout) -> None:
        """
        It's just a thin wrapper over the builtin print function, except that it prints
        strings with order numbers prepended.
        """
        print(bright_green(f"{self._index}. ") + s, file=file)
        self._index += 1

    @classmethod
    def null_logger(cls) -> Logger:
        ret = cls()
        ret.log = no_op
        return ret


def timefunc(fn: Callable[P, R]) -> Callable[P, R]:
    """
    A decorator to collect execution time statistics of the wrapped function.

    Statistics is stored in the `exe_time_statistics` attribute of the wrapped function.
    """

    statistics = {}

    def format_args(*args: P.args, **kwargs: P.kwargs) -> str:
        res = str(args).strip("()")
        if kwargs:
            res += ", " + str(kwargs).strip("{}")
        res = "(" + res + ")"
        return res

    @functools.wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        pre = time.time()
        result = fn(*args, **kwargs)
        post = time.time()

        statistics[format_args(*args, **kwargs)] = post - pre
        # print(f"Input is {format_args(*args, **kwargs)}, execution duration is {post-pre}")

        return result

    wrapper.exe_time_statistics = statistics
    return wrapper


def on_failure_raises(
    etype: type[Exception], error_message: str, suppress_cause: bool = False
) -> IdentityDecorator:
    """
    Return a decorator. Exception raised by the decorated function is caught
    and replaced by the new exception specified by the arguments to `on_failure_raises`.

    `error_message` is a format string, whose replacement fields are substituted for arguments
    to the decorated function.

    The `suppress_cause` flag specifies that the original exception raised by the
    decorated function should be suppressed. By default it's turned off.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        signature = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)

            except Exception as exc:
                arguments = signature.bind(*args, **kwargs).arguments
                formatted_error_message = error_message.format_map(arguments)
                cause = None if suppress_cause else exc
                raise etype(formatted_error_message) from cause

        return wrapper

    return decorator


def pause_at_exit(info: str = "Press any key to exit ...") -> None:
    atexit.register(lambda: click.pause(info=info))


def schedule_at_loop_close(aw: Awaitable[None]) -> None:
    loop = asyncio.get_running_loop()

    origin_shutdown_asyncgens = loop.shutdown_asyncgens

    async def shutdown_asyncgens(self) -> None:
        await aw
        await origin_shutdown_asyncgens()

    loop.shutdown_asyncgens = MethodType(shutdown_asyncgens, loop)


async def graceful_shutdown_client_session(session: aiohttp.ClientSession) -> None:
    # Ref: https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
    await session.close()
    print(dir(session))
    await asyncio.sleep(0.250)


def get_running_client_session(session_id: str) -> aiohttp.ClientSession:
    """
    "Why is creating a ClientSession outside of an event loop dangerous?
    Short answer is: life-cycle of all asyncio objects should be shorter than life-cycle of event loop."
    https://docs.aiohttp.org/en/stable/faq.html#why-is-creating-a-clientsession-outside-of-an-event-loop-dangerous

    Called inside coroutines
    """

    loop = asyncio.get_running_loop()

    if not hasattr(loop, "_aiohttp_client_sessions"):
        loop._aiohttp_client_sessions = {}

    try:
        return loop._aiohttp_client_sessions[session_id]
    except KeyError:
        session = aiohttp.ClientSession()
        loop._aiohttp_client_sessions[session_id] = session
        schedule_at_loop_close(graceful_shutdown_client_session(session))
        return session
