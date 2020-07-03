#!/usr/bin/env python3

import os
import re
import subprocess
import sys
from pathlib import Path

import click

sys.path.append(os.getcwd())
from fetcher.__version__ import __version__ as current_version
from fetcher.utils import parse_version_number
from scripts.release import main as release_main

# TODO bump version in setup.py


@click.command()
@click.argument("component")
@click.option("--release", is_flag=True, default=True)
def main(component: str, release: bool) -> None:
    print("Calculating new version......")

    major, minor, patch = parse_version_number(current_version)

    if component == "major":
        new_version = "v" + ".".join(map(str, (major + 1, 0, 0)))
    elif component == "minor":
        new_version = "v" + ".".join(map(str, (major, minor + 1, 0)))
    elif component == "patch":
        new_version = "v" + ".".join(map(str, (major, minor, patch + 1)))
    else:
        raise RuntimeError("Invalid argument")

    print("Bump the __version__ variable in __version__.py ......")
    p = Path("fetcher/__version__.py")
    old_content = p.read_text(encoding="utf-8")
    new_content = re.sub(
        r"__version__\s*=\s*\"(.*)\"", f'__version__ = "{new_version}"', old_content
    )
    p.write_text(new_content, encoding="utf-8")

    subprocess.run(["git", "add", "fetcher/__version__.py"]).check_returncode()
    print("Commiting the special commit for bumping version......")
    subprocess.run(
        ["git", "commit", "-m", f"Bump version to {new_version}"]
    ).check_returncode()
    print("Creating tag for new version......")
    subprocess.run(["git", "tag", new_version]).check_returncode()
    print("Pushing tag to remote......")
    subprocess.run(["git", "push", "origin", new_version]).check_returncode()

    if release:
        release_main(new_version)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
