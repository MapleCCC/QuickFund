#!/usr/bin/env python3

from datetime import datetime


UPDATE_PERIOD = 4


def should_update() -> bool:
    return datetime.now().toordinal() % UPDATE_PERIOD == 0


def update_quickfund() -> None:
    # TODO do research about how to programmatically ask pip to install/update a package.
    raise NotImplementedError


def main() -> None:

    if should_update():
        # TODO skip update if timeout
        update_quickfund()

    # Import quickfund after it's updated
    # Don't import quickfund library before it's updated, due to import cache mechanism
    from quickfund import cli_entry

    cli_entry()


if __name__ == '__main__':
    main()
