#!/usr/bin/env python3

import asyncio
import atexit
import functools
import subprocess
import sys
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from subprocess import CalledProcessError, TimeoutExpired
from typing import TYPE_CHECKING, TypeVar


try:
    from tqdm import trange
except ImportError:

    def trange_shim(n: int) -> Iterator[int]:
        for i in range(n):
            yield i
            # TODO
            raise NotImplementedError

    trange = trange_shim

if TYPE_CHECKING:
    from typing_extensions import ParamSpec
else:
    try:
        from typing_extensions import ParamSpec
    except ImportError:
        ParamSpec = TypeVar


P = ParamSpec("P")
R = TypeVar("R")


INSTALL_TIMEOUT = 60  # seconds

UPDATE_PERIOD = 5  # days
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


process_pool_executor = ProcessPoolExecutor()
atexit.register(process_pool_executor.shutdown)


async def asyncio_to_process(
    func: Callable[P, R], /, *args: P.args, **kwargs: P.kwargs
) -> R:
    """
    Asynchronously run function `func` in a separate process.
    Process version of the stdlib `asyncio.to_thread()`.
    """

    loop = asyncio.get_running_loop()
    pfunc = functools.partial(func, *args, **kwargs)

    return await loop.run_in_executor(process_pool_executor, pfunc)


def run_command_with_timeout_bar(command: Sequence[str], timeout: int) -> None:
    """Run command as subprocess, while displaying progressbar showing elapse of timeout count"""

    async def async_run_command(command: Sequence[str]) -> None:
        await asyncio_to_process(subprocess.check_call, command)

    async def display_timeout_bar(timeout: int) -> None:
        for second in trange(timeout):
            await asyncio.sleep(1)

    async def main() -> None:
        asyncio.gather(async_run_command(command), display_timeout_bar(timeout))

    asyncio.run(main())


def is_quickfund_installed() -> bool:
    try:
        import quickfund  # type: ignore
    except ImportError:
        return False
    else:
        return True


def install_quickfund() -> None:

    print("安装 QuickFund 库（这个过程大概执行十至六十秒）......")

    try:
        run_command_with_timeout_bar(UPDATE_COMMAND, INSTALL_TIMEOUT)

    except (CalledProcessError, TimeoutExpired):
        raise RuntimeError("安装 QuickFund 库失败，请重试")

    else:
        from quickfund import __version__

        print(f"成功安装 QuickFund 库最新版本 {__version__}")


def should_update() -> bool:
    return datetime.now().toordinal() % UPDATE_PERIOD == 0


def invalidate_import_cache(module_name: str) -> None:

    if module_name not in sys.modules:
        return

    del sys.modules[module_name]

    # Handle alias
    module = sys.modules[module_name]
    if module.__name__ != module_name:
        del sys.modules[module.__name__]

    # Handle submodules
    submodules = []
    for mod in sys.modules.keys():
        if mod.startswith(module_name + "."):
            submodules.append(mod)
    for mod in submodules:
        del sys.modules[mod]

    # Handle ascendants
    ascendants = []
    for mod in sys.modules.keys():
        if module_name.startswith(mod + "."):
            ascendants.append(mod)
    for mod in ascendants:
        del sys.modules[mod]


def update_quickfund() -> None:

    if not should_update():
        return

    print("检查更新（这个过程大概执行十至二十秒）......")

    from quickfund import __version__ as old_version

    try:
        run_command_with_timeout_bar(UPDATE_COMMAND, UPDATE_TIMEOUT)

    except (CalledProcessError, TimeoutExpired):
        print("更新失败，下次运行时将再次尝试更新")

    else:

        invalidate_import_cache("quickfund")

        from quickfund import __version__ as new_version

        if new_version == old_version:
            print("当前已是最新版本")
        else:
            print(f"更新完毕：QuickFund 库已更新至最新版本 {new_version}")


def main() -> None:

    if not is_quickfund_installed():
        install_quickfund()
    else:
        update_quickfund()

    from quickfund import cli_entry

    cli_entry()


if __name__ == "__main__":
    main()
