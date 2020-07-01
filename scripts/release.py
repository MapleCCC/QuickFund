#!/usr/bin/env python3
import subprocess

from main import RELEASE_EXECUTABLE_NAME, RELEASE_ASSET_NAME

PYINSTALLER_FLAGS = [
    "--name",
    RELEASE_EXECUTABLE_NAME,
    # "--upx-dir",
    # "D:\\Apps\\upx-3.96-win64",
    "--onefile",
]

subprocess.run(
    ["python", "-OO", "-m", "PyInstaller"] + PYINSTALLER_FLAGS + ["main.py"]
).check_returncode()
