import locale
import re
import traceback
from typing import Iterator, Tuple

from colorama import Fore, Style
from more_itertools import split_at

__all__ = [
    "bright_red",
    "bright_green",
    "bright_blue",
    "parse_version_number",
    "print_traceback_digest",
    "Logger",
]


def bright_red(s: str) -> str:
    return Style.BRIGHT + Fore.RED + s + Style.RESET_ALL  # type: ignore


def bright_green(s: str) -> str:
    return Style.BRIGHT + Fore.GREEN + s + Style.RESET_ALL  # type: ignore


def bright_blue(s: str) -> str:
    return Style.BRIGHT + Fore.BLUE + s + Style.RESET_ALL  # type: ignore


def parse_version_number(s: str) -> Tuple[int, int, int]:
    try:
        version_pattern = r"v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
        major, minor, patch = re.match(version_pattern, s).group(
            "major", "minor", "patch"
        )
        return int(major), int(minor), int(patch)
    except Exception as exc:
        raise RuntimeError("解析版本号时出现错误") from exc


def split_paragraphs(s: str) -> Iterator[str]:
    lines = s.splitlines()
    splits = split_at(lines, lambda line: line == "")
    for split in splits:
        yield "\n".join(split)


def retrieve_succinct_traceback(tb: str) -> str:
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
    }
}


def localize(s: str) -> str:
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
    def __init__(self) -> None:
        self._count = 1

    __slots__ = "_count"

    def log(self, s: str) -> None:
        print(bright_green(str(self._count) + ". ") + s)
        self._count += 1
