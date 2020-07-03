#!/usr/bin/env python3

import os
import subprocess
import sys

sys.path.append(os.getcwd())
from fetcher.__version__ import __version__
from fetcher.config import RELEASE_EXECUTABLE_NAME

PYINSTALLER_DISTPATH = "dist"

pyinstaller_flags = [
    # WARNING: using PyInstaller with upx enabled causes corrupted executable. Don't know why.
    # "--upx-dir",
    # "D:\\Apps\\upx-3.96-win64",
    "--noupx",
    "--distpath",
    PYINSTALLER_DISTPATH,
    "--clean",
    "--onefile",
]


def main(build_version: str = None) -> None:
    print("将 Python 脚本打包成可执行文件......")

    if not build_version:
        build_version = __version__

    basename, extension = os.path.splitext(RELEASE_EXECUTABLE_NAME)
    release_executable_name = basename + " " + build_version + extension

    subprocess.run(["make", "clean"]).check_returncode()
    subprocess.run(
        ["python", "-OO", "-m", "PyInstaller"]
        + pyinstaller_flags
        + ["--name", release_executable_name]
        + ["pyinstaller_entry.py"]
    ).check_returncode()


if __name__ == "__main__":
    main()
