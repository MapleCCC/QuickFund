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


def print_traceback_digest(colored: bool = True, localized: bool = True) -> None:
    tb = traceback.format_exc()
    digest = retrieve_succinct_traceback(tb)

    if localized:
        cause_msg = (
            "The above exception was the direct cause of the following exception:"
        )
        context_msg = (
            "During handling of the above exception, another exception occurred:"
        )
        local_lang = locale.getdefaultlocale()[0]

        if local_lang.startswith("en"):
            localized_digest = digest
        elif local_lang == "zh_CN":
            localized_digest_lines = []
            for line in digest.splitlines():
                if line == context_msg:
                    localized_digest_lines.append("在处理以上所述的错误时，发生了如下的另一个错误:")
                elif line == cause_msg:
                    localized_digest_lines.append("以上所述的错误直接引发了以下错误:")
                else:
                    line = line.replace("PermissionError", "权限错误")
                    line = line.replace("RuntimeError", "运行时错误")
                    localized_digest_lines.append(line)
            localized_digest = "\n".join(localized_digest_lines)
        else:
            raise NotImplementedError

        digest = localized_digest

    if colored:
        print(red(digest))
    else:
        print(digest)
