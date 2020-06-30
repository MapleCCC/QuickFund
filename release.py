#!/usr/bin/env python3
import subprocess

PYINSTALLER_FLAGS = [
    "--name",
    "基金信息生成器",
    "--upx-dir",
    "D:\\Apps\\upx-3.96-win64",
    "--onefile",
]

subprocess.run(
    ["python", "-OO", "-m", "PyInstaller"] + PYINSTALLER_FLAGS + ["main.py"]
).check_returncode()
