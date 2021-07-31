#!/usr/bin/env python3

import subprocess

import click


@click.command()
@click.argument("component")
def main(component: str) -> None:
    subprocess.run(["python", "scripts/bump_version.py", component]).check_returncode()
    subprocess.run(["python", "release.py"]).check_returncode()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
