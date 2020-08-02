#!/usr/bin/env python3

import os
import re
import shutil
import sys
import zipapp
from pathlib import Path

sys.path.append(os.getcwd())
from fetcher.__version__ import __version__

OUTPUT_FILENAME = f"基金信息生成器 {__version__}.pyz"
ZIPAPP_DISTPATH = "dist"
INPUT_PACKAGE = "fetcher"


# FIXME it's possible for current implementation to accidentally transform the relative import that is not
# actually relative import. For example, a relative import embedded in a string literal.
# The only robust and correct way to avoid such problem is to construct syntax tree
# using lexical analysis and syntax analysis.
def transform_relative_imports(p: Path) -> None:
    old_content = p.read_text(encoding="utf-8")
    pattern = r"from \.(?P<module>\w*) import (?P<names>.*)"
    repl = r"from \g<module> import \g<names>"
    new_content = re.sub(pattern, repl, old_content)
    p.write_text(new_content, encoding="utf-8")


def main() -> None:
    top_level_python_files = []
    for f in Path(INPUT_PACKAGE).iterdir():
        if f.is_file() and f.name.endswith(".py"):
            top_level_python_files.append(f)

    for f in top_level_python_files:
        shutil.copy2(f, f.name + ".bak")
        transform_relative_imports(f)

    if not os.path.isdir(ZIPAPP_DISTPATH):
        os.makedirs(ZIPAPP_DISTPATH)

    print("打包 Python 代码模块成可执行 archive......")
    zipapp.create_archive(
        INPUT_PACKAGE,
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

    for f in top_level_python_files:
        shutil.move(f.name + ".bak", f)


if __name__ == "__main__":
    main()
