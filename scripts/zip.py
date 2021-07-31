#!/usr/bin/env python3

import ast
import os
import re
import shutil
import sys
import zipapp
from pathlib import Path

sys.path.append(os.getcwd())
from quickfund.__version__ import __version__


OUTPUT_FILENAME = f"基金信息生成器 {__version__}.pyz"
ZIPAPP_DISTPATH = "dist"
INPUT_PACKAGE = "quickfund"


def transform_relative_imports(p: Path) -> None:
    class RelativeImportTransformer(ast.NodeTransformer):
        def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
            if node.level is None:
                return node

            if node.level > 0:
                node.level -= 1
            elif node.level == 0:
                pass
            else:
                raise RuntimeError("Unreachable")

            return node

    old_content = p.read_text(encoding="utf-8")

    try:
        tree = ast.parse(old_content)
    except SyntaxError as exc:
        raise ValueError(f"{p} has erroneous syntax: {exc.msg}")

    new_tree = RelativeImportTransformer().visit(tree)
    new_tree = ast.fix_missing_locations(new_tree)

    new_content = ast.unparse(new_tree)

    p.write_text(new_content, encoding="utf-8")


def main() -> None:
    top_level_python_files = Path(INPUT_PACKAGE).glob("*.py")

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
    #     main="quickfund.__main__:main",
    #     filter=lambda x: os.path.splitext(x)[1] == "py",
    #     compressed=True,
    # )

    for f in top_level_python_files:
        shutil.move(f.name + ".bak", f)


if __name__ == "__main__":
    main()
