#!/usr/bin/env python3

import os
import sys
from zipfile import ZipFile

from github import Github

sys.path.append(os.getcwd())
from fetcher.config import (
    RELEASE_ASSET_NAME,
    RELEASE_EXECUTABLE_NAME,
    REPO_NAME,
    REPO_OWNER,
)
from scripts.build import PYINSTALLER_DISTPATH
from scripts.build import main as build_main


def main(new_version: str) -> None:
    build_main()

    print("将可执行文件打包成压缩文件包......")

    asset_filepath = os.path.join(PYINSTALLER_DISTPATH, RELEASE_ASSET_NAME)
    executable_filepath = os.path.join(PYINSTALLER_DISTPATH, RELEASE_EXECUTABLE_NAME)

    # We don't compress, only package. Because the generated executable
    # doesn't have much to squeeze.
    with ZipFile(asset_filepath, "w") as f:
        f.write(executable_filepath)

    print("在 GitHub 仓库创建 Release......")

    # TODO when releasing, put in the message about what's updated, what's fixed,
    # and the hash signature of the assets.

    # Create release in GitHub. Upload the zip archive as release asset.
    user_name = input("Please enter GitHub account username: ").strip()
    password = input(
        f"Please input password for the GitHub account {user_name}: "
    ).strip()
    g = Github(user_name, password)
    repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
    git_release = repo.create_git_release(
        tag=new_version, name=new_version, message="Update"
    )

    print("上传打包好的可执行文件......")

    # TODO display upload progress (such as a progress bar)
    git_release.upload_asset(asset_filepath)
