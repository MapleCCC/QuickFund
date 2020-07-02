#!/usr/bin/env python3

import os
import subprocess
import sys

sys.path.append(os.getcwd())
from fetcher.config import RELEASE_EXECUTABLE_NAME

PYINSTALLER_DISTPATH = "dist"

pyinstaller_flags = [
    "--name",
    RELEASE_EXECUTABLE_NAME,
    # WARNING: using PyInstaller with upx enabled causes corrupted executable. Don't know why.
    # "--upx-dir",
    # "D:\\Apps\\upx-3.96-win64",
    "--noupx",
    "--distpath",
    PYINSTALLER_DISTPATH,
    "--clean",
    "--onefile",
]


def main():
    print("将 Python 脚本打包成可执行文件......")

    subprocess.run(["make", "clean"]).check_returncode()
    subprocess.run(
        ["python", "-OO", "-m", "PyInstaller"]
        + pyinstaller_flags
        + ["pyinstaller_entry.py"]
    ).check_returncode()


if __name__ == "__main__":
    main()
