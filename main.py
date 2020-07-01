import os
import re
from datetime import datetime
from enum import Enum, auto, unique
from pathlib import Path
from typing import Dict, Iterable

import click
import xlsxwriter
from tqdm import tqdm

from fetcher import get_fund_info
from utils import green, red


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


def write_to_xlsx(infos: Iterable[Dict[str, str]], xlsx_filename: str) -> None:
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
        for row, info in tqdm(list(enumerate(infos))):

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


@click.command()
@click.argument("filename")
@click.option("-o", "--output", default="基金信息.xlsx")
@click.option("-y", "--yes-to-all", is_flag=True, default=False)
def main(filename: str, output: str, yes_to_all: bool) -> None:
    in_filename = filename
    out_filename = output

    check_args(in_filename, out_filename, yes_to_all)

    print("获取基金代码列表......")
    codes = Path(in_filename).read_text(encoding="utf-8").splitlines()
    print("清洗基金代码列表......")
    codes = filter(lambda code: re.fullmatch(r"\d{6}", code), codes)

    print("获取基金相关信息......")
    infos = (get_fund_info(code) for code in tqdm(list(codes)))

    print("将基金相关信息写入 Excel 文件......")
    write_to_xlsx(infos, out_filename)

    # The emoji takes inspiration from the black (https://github.com/psf/black)
    print("完满结束! ✨ 🍰 ✨")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
