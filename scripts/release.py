#!/usr/bin/env python3

import os
import subprocess
import sys
from zipfile import ZipFile

sys.path.append(os.getcwd())
from fetcher.__main__ import RELEASE_ASSET_NAME, RELEASE_EXECUTABLE_NAME


PYINSTALLER_DISTPATH = "dist"

PYINSTALLER_FLAGS = [
    "--name",
    RELEASE_EXECUTABLE_NAME,
    # WARNING: using PyInstaller with upx enabled causes corrupted executable. Don't know why.
    # "--upx-dir",
    # "D:\\Apps\\upx-3.96-win64",
    "--dispath",
    PYINSTALLER_DISTPATH,
    "--clean",
    "--onefile",
]

subprocess.run(
    ["python", "-OO", "-m", "PyInstaller"] + PYINSTALLER_FLAGS + ["main.py"]
).check_returncode()

with ZipFile(os.path.join(PYINSTALLER_DISTPATH, RELEASE_ASSET_NAME), "w") as f:
    f.write(os.path.join(PYINSTALLER_DISTPATH, RELEASE_EXECUTABLE_NAME))
