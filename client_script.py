#!/usr/bin/env python3

import importlib
import subprocess
import sys
from datetime import datetime
from subprocess import CalledProcessError
from types import ModuleType


UPDATE_PERIOD = 4  # days
UPDATE_TIMEOUT = 20  # seconds


def should_update() -> bool:
    return datetime.now().toordinal() % UPDATE_PERIOD == 0


def incognito_import(name: str) -> ModuleType:
    module = importlib.import_module(name)

    # Detect alias
    # Reference: source of test.support.CleanImport https://github.com/python/cpython/blob/v3.9.0/Lib/test/support/__init__.py#L1241
    if module.__name__ != name:
        del sys.modules[module.__name__]

    del sys.modules[name]

    return module


def update_quickfund() -> None:

    print("检查更新（这个过程大概执行十至二十秒）......")

    old_version_info = incognito_import("quickfund").__version_info__

    commands = [
        "pip",
        "install",
        "--compile",
        "--upgrade-strategy",
        "eager",
        "--upgrade",
        "quickfund",
    ]

    try:
        # TODO display progress bar
        subprocess.check_call(commands, timeout=UPDATE_TIMEOUT)

    except (CalledProcessError, TimeoutError):
        print("更新失败，请稍后再试")

    else:
        from quickfund import __version__, __version_info__ as new_version_info

        if new_version_info == old_version_info:
            print("当前已是最新版本")
        elif new_version_info > old_version_info:
            print(f"更新完毕：QuickFund 库已更新至最新版本 {__version__}")
        else:
            raise RuntimeError("出现错误：竟更新至较低版本")


def main() -> None:

    if should_update():
        update_quickfund()

    # Import quickfund after it's updated
    # Don't import quickfund library before it's updated, due to import cache mechanism
    from quickfund import cli_entry

    cli_entry()


if __name__ == "__main__":
    main()
