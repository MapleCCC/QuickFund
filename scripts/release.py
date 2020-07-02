#!/usr/bin/env python3

import os
import subprocess
import sys
from zipfile import ZipFile

sys.path.append(os.getcwd())
from fetcher.config import RELEASE_ASSET_NAME, RELEASE_EXECUTABLE_NAME


PYINSTALLER_DISTPATH = "dist"

PYINSTALLER_FLAGS = [
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

print("将 Python 脚本打包成可执行文件......")

subprocess.run(
    ["python", "-OO", "-m", "PyInstaller"]
    + PYINSTALLER_FLAGS
    + ["pyinstaller_entry.py"]
).check_returncode()

print("将可执行文件打包成压缩文件包......")

# We don't compress, only package. Because the generated executable
# doesn't have much to squeeze.
with ZipFile(os.path.join(PYINSTALLER_DISTPATH, RELEASE_ASSET_NAME), "w") as f:
    f.write(os.path.join(PYINSTALLER_DISTPATH, RELEASE_EXECUTABLE_NAME))
