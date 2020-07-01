__all__ = ["red", "green", "blue"]


def red(s: str) -> str:
    return "\033[91m" + s + "\033[0m"


def green(s: str) -> str:
    return "\033[92m" + s + "\033[0m"


def blue(s: str) -> str:
    return "\033[94m" + s + "\033[0m"
