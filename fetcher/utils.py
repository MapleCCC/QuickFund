import functools
import inspect
import locale
import time
import traceback
from typing import Any, Callable, Iterator, Type

from colorama import Fore, Style
from more_itertools import split_at

__all__ = [
    "bright_red",
    "bright_green",
    "bright_blue",
    "print_traceback_digest",
    "Logger",
    "timefunc",
    "try_catch_raise",
]


def bright_red(s: str) -> str:
    """
    Augment a string, so that when printed to console, the string is displayed in bright red color.
    """
    return Style.BRIGHT + Fore.RED + s + Style.RESET_ALL  # type: ignore


def bright_green(s: str) -> str:
    """
    Augment a string, so that when printed to console, the string is displayed in bright green color.
    """
    return Style.BRIGHT + Fore.GREEN + s + Style.RESET_ALL  # type: ignore


def bright_blue(s: str) -> str:
    """
    Augment a string, so that when printed to console, the string is displayed in bright blue color.
    """
    return Style.BRIGHT + Fore.BLUE + s + Style.RESET_ALL  # type: ignore


def split_paragraphs(s: str) -> Iterator[str]:
    """
    Similar to splitlines(), except it splits paragraphs, not lines.
    """

    lines = s.splitlines()
    splits = split_at(lines, lambda line: line == "")
    for split in splits:
        yield "\n".join(split)


def retrieve_succinct_traceback(tb: str) -> str:
    """
    A utility that retrive succint traceback digest from a complete traceback string.
    """

    paragraphs = split_paragraphs(tb)
    digest = []
    for paragraph in paragraphs:
        digest.append(paragraph.splitlines()[-1])
    return "\n".join(digest)


localization_table = {
    "zh_CN": {
        "During handling of the above exception, another exception occurred:": "在处理以上所述的错误时，发生了如下的另一个错误:",
        "The above exception was the direct cause of the following exception:": "以上所述的错误直接引发了以下错误:",
        "PermissionError": "权限错误",
        "RuntimeError": "运行时错误",
        "KeyboardInterrupt": "来自键盘的中断信号",
        "Server Error": "服务器错误",
        "Press any key to exit ...": "按任意键以退出 ...",
    }
}


def localize(s: str) -> str:
    """
    Localize a string with a pre-defined translation dictionary.

    If we can't detect local langauge or we don't have translation dictionary for the
        given local language, we simply fall back to English.
    """

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
        pass
    else:
        translation_dict = localization_table[local_lang]
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

    tb = traceback.format_exc()
    digest = retrieve_succinct_traceback(tb)

    if localized:
        digest = localize(digest)

    if numbered:
        numbered_lines = []
        for i, line in enumerate(digest.splitlines(), start=1):
            numbered_lines.append(f"{i}. {line}")
        digest = "\n".join(numbered_lines)

    if indented:
        digest = "\n".join("    " + line for line in digest.splitlines())

    if colored:
        print(bright_red(digest))
    else:
        print(digest)


class Logger:
    """
    A lightweight logger.

    It's just a thin wrapper over the builtin print function, except that it prints
    strings with order numbers prepended.
    """

    def __init__(self) -> None:
        self._count = 1

    __slots__ = "_count"

    def log(self, s: str) -> None:
        """
        It's just a thin wrapper over the builtin print function, except that it prints
        strings with order numbers prepended.
        """
        print(bright_green(str(self._count) + ". ") + s)
        self._count += 1


def timefunc(fn: Callable) -> Callable:
    """
    A decorator to collect execution time statistics of the wrapped function.

    Statistics is stored in the `exe_time_statistics` attribute of the wrapped function.
    """

    statistics = {}

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        pre = time.time()
        result = fn(*args, **kwargs)
        post = time.time()

        format_args = str(args).strip("()")
        if kwargs:
            format_args += ", " + str(kwargs).strip("{}")
        format_args = "(" + format_args + ")"

        # print(f"Input is {format_args}, execution duration is {post-pre}")
        statistics[format_args] = post - pre

        return result

    wrapper.exe_time_statistics = statistics  # type: ignore
    return wrapper


# FIXME the default value for the ctx parameter should be "context", not "cause"
# TODO add argument to control which exceptions to catch
def try_catch_raise(
    new_except: Type[Exception], err_msg: str, ctx: str = "cause"
) -> Callable[[Callable], Callable]:
    def decorator(fn: Callable) -> Callable:
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                ba = sig.bind(*args, **kwargs)
                err_msg = err_msg.format_map(ba.arguments)

                if ctx == "cause":
                    raise new_except(err_msg) from exc
                elif ctx == "suppress":
                    raise new_except(err_msg) from None
                elif ctx == "context":
                    raise new_except(err_msg)
                else:
                    raise ValueError(
                        "Valid values for the `ctx` parameter are `cause`, `suppress`, and `context`."
                    )

        return wrapper

    return decorator
