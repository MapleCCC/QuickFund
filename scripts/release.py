#!/usr/bin/env python3

import os
import subprocess
from zipfile import ZipFile

from main import RELEASE_ASSET_NAME, RELEASE_EXECUTABLE_NAME

PYINSTALLER_DEFAULT_DISTPATH = "dist"

PYINSTALLER_FLAGS = [
    "--name",
    RELEASE_EXECUTABLE_NAME,
    # WARNING: using PyInstaller with upx enabled causes corrupted executable. Don't know why.
    # "--upx-dir",
    # "D:\\Apps\\upx-3.96-win64",
    "--onefile",
]

# TODO do some manipulation to tqdm library to remove unnecessary heavyweight
# dependencies and hence reduce size of the generated executable.

subprocess.run(
    ["python", "-OO", "-m", "PyInstaller"] + PYINSTALLER_FLAGS + ["main.py"]
).check_returncode()

with ZipFile(os.path.join(PYINSTALLER_DEFAULT_DISTPATH, RELEASE_ASSET_NAME), "w") as f:
    f.write(os.path.join(PYINSTALLER_DEFAULT_DISTPATH, RELEASE_EXECUTABLE_NAME))
