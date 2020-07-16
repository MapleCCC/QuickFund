import locale
import re
import traceback
from typing import Iterator, Tuple

from more_itertools import split_at

__all__ = ["red", "green", "blue", "parse_version_number", "print_traceback_digest"]


def red(s: str) -> str:
    return "\033[91m" + s + "\033[0m"


def green(s: str) -> str:
    return "\033[92m" + s + "\033[0m"


def blue(s: str) -> str:
    return "\033[94m" + s + "\033[0m"


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
    }
}


def print_traceback_digest(colored: bool = True, localized: bool = True) -> None:
    tb = traceback.format_exc()
    digest = retrieve_succinct_traceback(tb)

    if localized:
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
                digest = digest.replace(src, dst)

    if colored:
        print(red(digest))
    else:
        print(digest)
