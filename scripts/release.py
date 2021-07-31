#!/usr/bin/env python3

import os
import sys
from zipfile import ZipFile

import click
from github import Github

sys.path.append(os.getcwd())
from quickfund.config import (
    RELEASE_ASSET_NAME,
    RELEASE_EXECUTABLE_NAME,
    REPO_NAME,
    REPO_OWNER,
)
from scripts._local_credentials import github_account_access_token


# TODO upload source tar ball, not executable


def release(new_version: str, upload_executable: bool = False) -> None:
    print("在 GitHub 仓库创建 Release......")

    # TODO when releasing, put in the message about what's updated, what's fixed,
    # and the hash signature of the assets.

    # Create release in GitHub. Upload the zip archive as release asset.
    g = Github(github_account_access_token)
    repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
    git_release = repo.create_git_release(
        tag=new_version,
        name=new_version,
        message="For detail changelog, please consult commit history, and commit messages.",
    )

    if upload_executable:
        print("将 Python 脚本打包成可执行文件......")
        build_main(new_version)

        print("将可执行文件打包成压缩文件包......")

        basename, extension = os.path.splitext(RELEASE_EXECUTABLE_NAME)
        release_executable_name = basename + " " + new_version + extension
        basename, extension = os.path.splitext(RELEASE_ASSET_NAME)
        release_asset_name = basename + " " + new_version + extension

        asset_filepath = os.path.join(PYINSTALLER_DISTPATH, release_asset_name)
        executable_filepath = os.path.join(
            PYINSTALLER_DISTPATH, release_executable_name
        )

        # We don't compress, only package. Because the generated executable
        # doesn't have much to squeeze.
        with ZipFile(asset_filepath, "w") as f:
            f.write(executable_filepath)

        print("上传打包好的可执行文件......")

        # TODO display upload progress (such as a progress bar)
        # TODO open issue or PR in PyGithub repository
        git_release.upload_asset(asset_filepath)


@click.command()
@click.argument("new_version")
def main(new_version: str) -> None:
    release(new_version)


if __name__ == "__main__":
    main()
