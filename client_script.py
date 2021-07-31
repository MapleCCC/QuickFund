from datetime import datetime

import click
from quickfund import cli_entry


UPDATE_PERIOD = 4


def should_update() -> bool:
    return datetime.now().date().toordinal() % UPDATE_PERIOD == 0


def update_quickfund() -> None:
    # TODO do research about how to programmatically ask pip to install/update a package.
    raise NotImplementedError


@click.command()
@click.argument("file", nargs=1)
def main(file: str) -> None:

    if should_update():
        update_quickfund()

    cli_entry(file)
