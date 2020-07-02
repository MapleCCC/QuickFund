#!/usr/bin/env python3

import os
import subprocess
import sys
from zipfile import ZipFile

from github import Github

sys.path.append(os.getcwd())
from fetcher.config import (
    RELEASE_ASSET_NAME,
    RELEASE_EXECUTABLE_NAME,
    REPO_NAME,
    REPO_OWNER,
    __version__,
)


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
g = Github("MapleCCC", "im5Pos$sible")
repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
git_release = repo.create_git_release(
    tag=__version__, name=__version__, message="Update"
)

print("上传打包好的可执行文件......")

git_release.upload_asset(asset_filepath)
