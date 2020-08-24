#!/usr/bin/env python3

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List

import click
import semver

sys.path.append(os.getcwd())
from fetcher.__version__ import __version__ as current_version
from scripts.release import release


def bump_file(filename: str, pattern: str, repl: str) -> None:
    p = Path(filename)
    old_content = p.read_text(encoding="utf-8")
    new_content = re.sub(pattern, repl, old_content)
    p.write_text(new_content, encoding="utf-8")


def bump_file___version__(new_version: str) -> None:
    pattern = r"__version__\s*=\s*\"(.*)\""
    repl = f'__version__ = "{new_version}"'
    bump_file("fetcher/__version__.py", pattern, repl)


def bump_file_README(new_version: str) -> None:
    pattern = r"github.com/MapleCCC/Fund-Info-Fetcher/compare/.*\.\.\.master"
    repl = f"github.com/MapleCCC/Fund-Info-Fetcher/compare/{new_version}...master"
    bump_file("README.md", pattern, repl)

    pattern = r"git\+https://github\.com/MapleCCC/Fund-Info-Fetcher\.git@.*#egg=Fund-Info-Fetcher"
    repl = f"git+https://github.com/MapleCCC/Fund-Info-Fetcher.git@{new_version}#egg=Fund-Info-Fetcher"
    bump_file("README.md", pattern, repl)


def run(cmd: List[str]) -> None:
    subprocess.run(cmd).check_returncode()


def contains_uncommitted_change(filepath: str):
    # Add non-existent file check/guard, because `git status --porcelain` has
    # similar output for both unmodified file and non-existent file
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Can't get status of non-existent file: {filepath}")

    cmpl_proc = subprocess.run(
        ["git", "status", "--porcelain", "--no-renames", "--", filepath],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if cmpl_proc.returncode != 0:
        raise RuntimeError(f"Error getting status of {filepath}")

    return cmpl_proc.stdout[:2] != "  "


@click.command()
@click.argument("component")
@click.option("--no-release", is_flag=True)
def main(component: str, no_release: bool) -> None:
    print("Calculating new version......")

    old_version_info = semver.VersionInfo.parse(current_version.lstrip("v"))

    method = getattr(old_version_info, f"bump_{component}", None)
    if method is None:
        raise ValueError(
            "Invalid value for argument `component`. "
            "Valid values are `major`, `minor`, `patch`, and `prerelease`."
        )
    new_version_info = method()

    new_version = "v" + str(new_version_info)

    print("Bump the __version__ variable in __version__.py ......")
    bump_file___version__(new_version)

    print("Bump version-related information in README.md ......")
    bump_file_README(new_version)

    run(["git", "add", "fetcher/__version__.py"])

    if contains_uncommitted_change("README.md"):
        raise RuntimeError(
            "README.md contains uncommitted change. "
            "Please clean it up before rerun the script."
        )
    run(["git", "add", "README.md"])

    print("Committing the special commit for bumping version......")
    run(["git", "commit", "-m", f"Bump version to {new_version}"])

    print("Creating tag for new version......")
    run(["git", "tag", new_version])

    # TODO if we change from using subprocess.run to using PyGithub,
    # will the time cost be shorter?
    print("Pushing tag to remote......")
    run(["git", "push", "origin", new_version])

    if not no_release:
        release(new_version)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
