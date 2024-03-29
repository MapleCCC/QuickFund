from __future__ import annotations

import atexit
import functools
import inspect
import locale
import sys
import traceback
from collections.abc import Callable
from typing import IO, TypeVar

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
    "on_failure_raises",
    "pause_at_exit",
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
    Similar to str.splitlines(), except it splits paragraphs, not lines.

    Returns empty list for empty string.
    A terminal paragraph boundary doesn't result in an extra paragraph.
    """

    if not text:
        return []

    paras = regex.split(r"\n{2,}", text)

    if len(paras) > 1 and paras[-1] == "":
        paras.pop()

    return paras


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

    # Line numbers are intentionally not colored, for readability.
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


def noop(*_, **__) -> None:
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
        ret.log = noop
        return ret


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
