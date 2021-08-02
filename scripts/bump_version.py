#!/usr/bin/env python3

import os
import re
import subprocess
import sys
from pathlib import Path

import click
import semver

sys.path.append(os.getcwd())
from quickfund.__version__ import __version__ as current_version
from quickfund.utils import Logger
from scripts.release import release


# TODO use PyGithub instead of naive subprocess.run


logger = Logger()


def bump_file(filename: str, pattern: str, repl: str) -> None:
    p = Path(filename)
    old_content = p.read_text(encoding="utf-8")
    new_content = re.sub(pattern, repl, old_content)
    p.write_text(new_content, encoding="utf-8")


def bump_file___version__(new_version: str) -> None:
    pattern = r"__version__\s*=\s*\"(.*)\""
    repl = f'__version__ = "{new_version}"'
    bump_file("quickfund/__version__.py", pattern, repl)


def bump_file_README(new_version: str) -> None:
    pattern = r"github.com/MapleCCC/QuickFund/compare/.*\.\.\.master"
    repl = f"github.com/MapleCCC/QuickFund/compare/{new_version}...master"
    bump_file("README.md", pattern, repl)

    pattern = r"git\+https://github\.com/MapleCCC/QuickFund\.git@.*#egg=QuickFund"
    repl = f"git+https://github.com/MapleCCC/QuickFund.git@{new_version}#egg=QuickFund"
    bump_file("README.md", pattern, repl)


def run(cmd: list[str]) -> None:
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

    return len(cmpl_proc.stdout) != 0


@click.command()
@click.argument("component")
@click.option("--no-release", is_flag=True)
def main(component: str, no_release: bool) -> None:
    if contains_uncommitted_change("README.md"):
        raise RuntimeError(
            "README.md contains uncommitted change. "
            "Please clean it up before rerun the script."
        )

    logger.log("Calculating new version......")

    old_version_info = semver.VersionInfo.parse(current_version.lstrip("v"))
    if component == "major":
        new_version_info = old_version_info.bump_major()
    elif component == "minor":
        new_version_info = old_version_info.bump_minor()
    elif component == "patch":
        new_version_info = old_version_info.bump_patch()
    elif component == "prerelease":
        new_version_info = old_version_info.bump_prerelease()
    else:
        raise ValueError(
            "Invalid value for argument `component`. "
            "Valid values are `major`, `minor`, `patch`, and `prerelease`."
        )

    new_version = "v" + str(new_version_info)

    logger.log("Bump the __version__ variable in __version__.py ......")
    bump_file___version__(new_version)

    logger.log("Bump version-related information in README.md ......")
    bump_file_README(new_version)

    run(["git", "add", "quickfund/__version__.py"])

    run(["git", "add", "README.md"])

    logger.log("Committing the special commit for bumping version......")
    run(["git", "commit", "-m", f"Bump version to {new_version}"])

    logger.log("Creating tag for new version......")
    run(["git", "tag", new_version])

    # TODO if we change from using subprocess.run to using PyGithub,
    # will the time cost be shorter?
    logger.log("Pushing tag to remote......")
    run(["git", "push", "origin", new_version])

    if not no_release:
        release(new_version)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
