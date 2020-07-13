#!/usr/bin/env python3

import re
import os
import shutil
import sys
import zipapp
from pathlib import Path

sys.path.append(os.getcwd())
from fetcher.__version__ import __version__


OUTPUT_FILENAME = f"基金信息生成器 {__version__}.pyz"
ZIPAPP_DISTPATH = "dist"
ENTRY_FILE = "fetcher/__main__.py"
ENTRY_FILE_BACKUP = ENTRY_FILE + ".bak"


def transform_relative_imports(file: str) -> None:
    p = Path(file)
    old_content = p.read_text(encoding="utf-8")
    new_lines = []
    for line in old_content.splitlines():
        matchobj = re.fullmatch(r"from \.(?P<module>\w*) import (?P<names>.*)", line)
        if matchobj:
            module_name, imported_names = matchobj.group("module", "names")
            new_lines.append(f"from {module_name} import {imported_names}")
        else:
            new_lines.append(line)
    new_content = "\n".join(new_lines)
    p.write_text(new_content, encoding="utf-8")


def main() -> None:
    shutil.copy2(ENTRY_FILE, ENTRY_FILE_BACKUP)

    transform_relative_imports(ENTRY_FILE)

    if not os.path.isdir(ZIPAPP_DISTPATH):
        os.makedirs(ZIPAPP_DISTPATH)

    print("打包 Python 代码模块成可执行 archive......")
    zipapp.create_archive(
        "fetcher",
        os.path.join(ZIPAPP_DISTPATH, OUTPUT_FILENAME),
        interpreter="/usr/bin/env python3",
        compressed=True,
    )

    # zipapp.create_archive(
    #     os.getcwd(),
    #     "基金信息生成器.pyz",
    #     interpreter="/usr/bin/env python3",
    #     main="fetcher.__main__:main",
    #     filter=lambda x: os.path.splitext(x)[1] == "py",
    #     compressed=True,
    # )

    shutil.move(ENTRY_FILE_BACKUP, ENTRY_FILE)


if __name__ == "__main__":
    main()
