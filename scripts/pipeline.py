#!/usr/bin/env python3

import subprocess

import click


@click.command()
@click.argument("component")
def main(component: str) -> None:
    subprocess.run(["python", "scripts/bump_version.py", component]).check_returncode()
    subprocess.run(["python", "scripts/build.py"]).check_returncode()
    subprocess.run(["python", "scripts/up_ftp_server.py"]).check_returncode()


if __name__ == "__main__":
    main()
