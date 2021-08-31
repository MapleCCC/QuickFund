#!/usr/bin/env python3

import subprocess
import sys
from datetime import datetime
from subprocess import CalledProcessError, TimeoutExpired


UPDATE_PERIOD = 4  # days
UPDATE_TIMEOUT = 20  # seconds


INSTALL_COMMAND = UPDATE_COMMAND = [
    "pip",
    "install",
    "--compile",
    "--upgrade-strategy",
    "eager",
    "--upgrade",
    "quickfund",
]


def should_update() -> bool:
    return datetime.now().toordinal() % UPDATE_PERIOD == 0


def update_quickfund() -> None:

    if not should_update():
        return

    print("检查更新（这个过程大概执行十至二十秒）......")

    from quickfund import __version_info__ as old_version_info

    try:
        # TODO display progress bar
        subprocess.check_call(UPDATE_COMMAND, timeout=UPDATE_TIMEOUT)

    except (CalledProcessError, TimeoutExpired):
        print("更新失败，下次运行时将再次尝试更新")

    else:

        # Invalidate import cache
        del sys.modules["quickfund"]

        from quickfund import __version__, __version_info__ as new_version_info

        if new_version_info == old_version_info:
            print("当前已是最新版本")
        elif new_version_info > old_version_info:
            print(f"更新完毕：QuickFund 库已更新至最新版本 {__version__}")
        else:
            raise RuntimeError("出现错误：竟不正确地更新至较低版本！")


def is_quickfund_installed() -> bool:
    try:
        import quickfund  # type: ignore
    except ImportError:
        return False
    else:
        return True


def install_quickfund() -> None:
    try:
        subprocess.check_call(UPDATE_COMMAND)

    except CalledProcessError:
        raise RuntimeError("安装 QuickFund 库失败，请重试")

    else:
        from quickfund import __version__

        print(f"成功安装 QuickFund 库最新版本 {__version__}")


def main() -> None:

    if not is_quickfund_installed():
        install_quickfund()
    else:
        update_quickfund()

    from quickfund import cli_entry

    cli_entry()


if __name__ == "__main__":
    main()
