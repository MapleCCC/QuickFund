import atexit
import os
import re
import shutil
from datetime import datetime
from enum import Enum, auto, unique
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Tuple
from zipfile import ZipFile

import click
import xlsxwriter
from tqdm import tqdm

from fetcher import get_fund_info
from github_utils import get_latest_released_asset, get_latest_released_version
from utils import green, red

__version__ = "0.2.0"

RELEASE_ASSET_NAME = "fund-info-fetcher-win64.zip"
RELEASE_EXECUTABLE_NAME = "基金信息生成器.exe"

REPO_URL_USER = "MapleCCC"
REPO_URL_REPO = "Fund-Info-Fetcher"


@unique
class ExcelCellDataType(Enum):
    string = auto()
    date = auto()
    number = auto()


# TODO use language construct to make sure fieldnames consistent with
# their occurrences in other places across the code repository.

fieldnames = ["基金名称", "基金代码", "净值日期", "单位净值", "日增长率", "估算日期", "实时估值", "估算增长率", "分红送配"]
fieldtypes = [
    ExcelCellDataType.string,
    ExcelCellDataType.string,
    ExcelCellDataType.date,
    ExcelCellDataType.number,
    ExcelCellDataType.string,
    ExcelCellDataType.string,
    ExcelCellDataType.number,
    ExcelCellDataType.string,
    ExcelCellDataType.string,
]


def pause_wait_enter() -> None:
    # input("Press ENTER to exit")
    input("按下回车键以退出")


atexit.register(pause_wait_enter)


def parse_version_number(s: str) -> Tuple[int, int, int]:
    try:
        version_pattern = r"v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
        major, minor, patch = re.match(version_pattern, s).group(
            "major", "minor", "patch"
        )
        return int(major), int(minor), int(patch)
    except Exception as exc:
        raise RuntimeError("解析版本号是出现错误") from exc


def write_to_xlsx(infos: List[Dict[str, str]], xlsx_filename: str) -> None:
    try:
        print("新建 Excel 文档......")
        workbook = xlsxwriter.Workbook(xlsx_filename)
        worksheet = workbook.add_worksheet()

        header_format = workbook.add_format(
            {"bold": True, "align": "center", "valign": "top", "border": 1}
        )
        date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})

        # Writer header
        print("写入文档头......")
        for i, fieldname in enumerate(fieldnames):
            worksheet.write(0, i, fieldname, header_format)

        # Widen column for date data
        for i, fieldtype in enumerate(fieldtypes):
            if fieldtype == ExcelCellDataType.date:
                worksheet.set_column(i, i, 13)

        # Widen column for fund name field
        for i, fieldname in enumerate(fieldnames):
            if fieldname == "基金名称":
                worksheet.set_column(i, i, 22)
            elif fieldname == "估算日期":
                worksheet.set_column(i, i, 17)
            elif fieldname in ("实时估值", "估算增长率"):
                worksheet.set_column(i, i, 11)

        # Write body
        print("写入文档体......")
        for row, info in tqdm(enumerate(infos)):

            for col, fieldname in enumerate(fieldnames):
                fieldvalue = info[fieldname]
                fieldtype = fieldtypes[col]

                if fieldtype == ExcelCellDataType.string:
                    worksheet.write_string(row + 1, col, fieldvalue)
                elif fieldtype == ExcelCellDataType.number:
                    num = float(fieldvalue)
                    worksheet.write_number(row + 1, col, num)
                elif fieldtype == ExcelCellDataType.date:
                    date = datetime.strptime(fieldvalue, "%Y-%m-%d")
                    worksheet.write_datetime(row + 1, col, date, date_format)
                else:
                    raise RuntimeError("Unreachable")

        workbook.close()
    except Exception as exc:
        raise RuntimeError(f"获取基金信息并写入 Excel 文档的时候发生错误") from exc


def check_args(in_filename: str, out_filename: str, yes_to_all: bool) -> None:
    if not os.path.exists(in_filename):
        raise FileNotFoundError(f"文件 {in_filename} 不存在")

    if os.path.isdir(out_filename):
        raise RuntimeError(f"同名文件夹已存在，无法新建文件 {out_filename}")

    if os.path.isfile(out_filename) and not yes_to_all:
        while True:
            choice = input(
                f"{out_filename} 同名文件已存在，是否覆盖之？【选择是请输入“{green('是')}”，选择否请输入“{red('否')}”】\n"
            ).strip()
            if choice == "是":
                break
            elif choice == "否":
                exit()
            else:
                print("输入指令无效，请重新输入")


def update(latest_version: str) -> None:
    try:
        print("开始更新程序......")
        with TemporaryDirectory() as d:
            tempdir = Path(d)
            p = tempdir / RELEASE_ASSET_NAME
            p.write_bytes(
                get_latest_released_asset(
                    REPO_URL_USER, REPO_URL_REPO, RELEASE_ASSET_NAME
                )
            )
            # WARNING: A big pitfall here is that Python's builtin zipfile module
            # has a flawed implementation of decoding zip file member names.
            # Solution appeals to
            # https://stackoverflow.com/questions/41019624/python-zipfile-module-cant-extract-filenames-with-chinese-characters
            transformed_executable_name = RELEASE_EXECUTABLE_NAME.encode("gbk").decode(
                "cp437"
            )
            with ZipFile(p) as f:
                f.extract(transformed_executable_name, path=str(tempdir))
            basename, extension = os.path.splitext(RELEASE_EXECUTABLE_NAME)
            versioned_executable_name = basename + latest_version + extension
            shutil.move(
                tempdir / transformed_executable_name,  # type: ignore
                Path.cwd() / versioned_executable_name,
            )
        print("程序更新完毕")
    except Exception as exc:
        raise RuntimeError(f"更新程序的时候发生错误") from exc


def check_update() -> None:
    print("获取最新分发版本......")
    latest_version = get_latest_released_version(REPO_URL_USER, REPO_URL_REPO)
    if parse_version_number(latest_version) > parse_version_number(__version__):
        while True:
            choice = input(
                f"检测到更新版本 {latest_version}，是否更新？【选择是请输入“{green('是')}”，选择否请输入“{red('否')}”】\n"
            ).strip()
            if choice == "是":
                update(latest_version)
                exit()
            elif choice == "否":
                return
            else:
                print("输入指令无效，请重新输入")
    else:
        print("当前已是最新版本")


@click.command()
@click.argument("filename")
@click.option("-o", "--output", default="基金信息.xlsx")
@click.option("-y", "--yes-to-all", is_flag=True, default=False)
@click.option("--disable-check-update", is_flag=True, default=False)
# TODO: @click.option("--update")
@click.version_option(version=__version__)
def main(
    filename: str, output: str, yes_to_all: bool, disable_check_update: bool
) -> None:
    if not disable_check_update:
        print("检查更新......")
        check_update()

    in_filename = filename
    out_filename = output

    print("检查参数......")
    check_args(in_filename, out_filename, yes_to_all)

    print("获取基金代码列表......")
    codes = Path(in_filename).read_text(encoding="utf-8").splitlines()
    print("清洗基金代码列表......")
    codes = list(filter(lambda code: re.fullmatch(r"\d{6}", code), tqdm(codes)))

    print("获取基金相关信息......")
    infos = [get_fund_info(code) for code in tqdm(codes)]

    print("将基金相关信息写入 Excel 文件......")
    write_to_xlsx(infos, out_filename)

    # The emoji takes inspiration from the black (https://github.com/psf/black)
    print("完满结束! ✨ 🍰 ✨")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
