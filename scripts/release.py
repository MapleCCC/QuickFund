#!/usr/bin/env python3

import os
import subprocess
import sys
from zipfile import ZipFile

sys.path.append(os.getcwd())
from fetcher.config import (
    __version__,
    RELEASE_ASSET_NAME,
    RELEASE_EXECUTABLE_NAME,
    REPO_OWNER,
    REPO_NAME,
)
from fetcher.github_utils import create_release, get_latest_release_id, upload_asset


pyinstaller_distpath = "dist"

pyinstaller_flags = [
    "--name",
    RELEASE_EXECUTABLE_NAME,
    # WARNING: using PyInstaller with upx enabled causes corrupted executable. Don't know why.
    # "--upx-dir",
    # "D:\\Apps\\upx-3.96-win64",
    "--noupx",
    "--distpath",
    pyinstaller_distpath,
    "--clean",
    "--onefile",
]

print("将 Python 脚本打包成可执行文件......")

subprocess.run(
    ["python", "-OO", "-m", "PyInstaller"]
    + pyinstaller_flags
    + ["pyinstaller_entry.py"]
).check_returncode()

print("将可执行文件打包成压缩文件包......")

asset_filepath = os.path.join(pyinstaller_distpath, RELEASE_ASSET_NAME)
executable_filepath = os.path.join(pyinstaller_distpath, RELEASE_EXECUTABLE_NAME)

# We don't compress, only package. Because the generated executable
# doesn't have much to squeeze.
with ZipFile(asset_filepath, "w") as f:
    f.write(executable_filepath)

print("在 GitHub 仓库创建 Release")

# Create release in GitHub. Upload the zip archive as release asset.
create_release(REPO_OWNER, REPO_NAME, __version__)

print("上传打包好的可执行文件......")

latest_release_id = get_latest_release_id(REPO_OWNER, REPO_NAME)
upload_asset(
    REPO_OWNER,
    REPO_NAME,
    latest_release_id,
    asset_filepath,
    content_type="application/zip",
)
