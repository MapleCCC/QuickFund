import re
from typing import Tuple

__all__ = ["red", "green", "blue", "parse_version_number"]


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
