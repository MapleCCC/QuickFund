#!/usr/bin/env python3

import atexit
import locale
import os
import re
import shelve
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timedelta
from enum import Enum, auto, unique
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, TypeVar

import click
import xlsxwriter
from tqdm import tqdm, trange

from .__version__ import __version__
from .config import REPO_NAME, REPO_OWNER
from .fetcher import fetch_estimate, fetch_fund_info, fetch_net_value
from .github_utils import get_latest_release_version
from .lru import LRU
from .utils import parse_version_number


if locale.getdefaultlocale()[0] == "zh_CN":
    PERSISTENT_CACHE_DB_DIRECTORY = ".缓存"
else:
    PERSISTENT_CACHE_DB_DIRECTORY = ".cache"
# Instead of using full filename, we use basename, because shelve requires so.
PERSISTENT_CACHE_DB_FILE_BASENAME = "cache"
PERSISTENT_CACHE_DB_RECORD_MAX_NUM = 2000


# FIXME The problem is that there is no officially supported way to type annotate a
# function with optional argument.
T = TypeVar("T")
tqdm: Callable[[Iterable[T]], Iterator[T]]


@unique
class ExcelCellDataType(Enum):
    string = auto()
    date = auto()
    number = auto()


# TODO use language construct to make sure fieldnames consistent with
# their occurrences in other places across the code repository. As
# manually syncing them is both tedious and error-prone.

fieldnames = [
    "基金名称",
    "基金代码",
    "上一天净值日期",
    "上一天净值",
    "净值日期",
    "单位净值",
    "日增长率",
    "估算日期",
    "实时估值",
    "估算增长率",
    "分红送配",
]
fieldtypes = [
    ExcelCellDataType.string,
    ExcelCellDataType.string,
    ExcelCellDataType.date,
    ExcelCellDataType.number,
    ExcelCellDataType.date,
    ExcelCellDataType.number,
    ExcelCellDataType.string,
    ExcelCellDataType.date,
    ExcelCellDataType.number,
    ExcelCellDataType.string,
    ExcelCellDataType.string,
]


# TODO refactor write_to_xlsx. Such a long function is prone to error and grows
# harder to maintain.
def write_to_xlsx(fund_infos: List[Dict[str, str]], xlsx_filename: str) -> None:
    try:
        print("新建 Excel 文档......")
        workbook = xlsxwriter.Workbook(xlsx_filename)
        worksheet = workbook.add_worksheet()

        header_format = workbook.add_format(
            {"bold": True, "align": "center", "valign": "top", "border": 1}
        )
        date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})
        datetime_format = workbook.add_format({"num_format": "yyyy-mm-dd hh:mm"})
        yellow_highlight_format = workbook.add_format({"bg_color": "yellow"})
        blue_highlight_format = workbook.add_format({"bg_color": "B4D6E4"})

        # Writer header
        print("写入文档头......")
        for i, fieldname in enumerate(fieldnames):
            worksheet.write(0, i, fieldname, header_format)

        # Widen column for fund name field
        for i, fieldname in enumerate(fieldnames):
            if fieldname == "基金名称":
                worksheet.set_column(i, i, 22)
            elif fieldname == "估算日期":
                worksheet.set_column(i, i, 17)
            elif fieldname in ("实时估值", "估算增长率"):
                worksheet.set_column(i, i, 11)
            elif fieldname == "上一天净值":
                worksheet.set_column(i, i, 10)
            elif fieldname == "上一天净值日期":
                worksheet.set_column(i, i, 14)
            elif fieldname == "净值日期":
                worksheet.set_column(i, i, 13)

        # Write body
        print("写入文档体......")
        for row, info in enumerate(tqdm(fund_infos)):

            for col, fieldname in enumerate(fieldnames):
                fieldvalue = info[fieldname]
                fieldtype = fieldtypes[col]

                if fieldtype == ExcelCellDataType.string:
                    worksheet.write_string(row + 1, col, fieldvalue)
                elif fieldtype == ExcelCellDataType.number:
                    try:
                        num = float(fieldvalue)
                    except ValueError:
                        raise RuntimeError(
                            f'基金代码为 {info["基金代码"]} 的基金"{info["基金名称"]}"的"{fieldname}"数据无法转换成浮点数格式：{fieldvalue}'
                        )
                    if fieldname in ("上一天净值", "单位净值"):
                        worksheet.write_number(
                            row + 1, col, num, yellow_highlight_format
                        )
                    elif fieldname == "实时估值":
                        worksheet.write_number(row + 1, col, num, blue_highlight_format)
                    else:
                        worksheet.write_number(row + 1, col, num)
                elif fieldtype == ExcelCellDataType.date:
                    if fieldname in ("净值日期", "上一天净值日期"):
                        net_value_date = datetime.strptime(
                            fieldvalue, "%Y-%m-%d"
                        ).date()
                        worksheet.write_datetime(
                            row + 1, col, net_value_date, date_format
                        )
                    elif fieldname == "估算日期":
                        estimate_datetime = datetime.strptime(
                            fieldvalue, "%Y-%m-%d %H:%M"
                        )
                        worksheet.write_datetime(
                            row + 1, col, estimate_datetime, datetime_format
                        )
                    else:
                        raise RuntimeError("Unreachable")
                else:
                    raise RuntimeError("Unreachable")

        workbook.close()
    except Exception as exc:
        raise RuntimeError(f"获取基金信息并写入 Excel 文档的时候发生错误") from exc


def check_args(in_filename: str, out_filename: str) -> None:
    if not os.path.exists(in_filename):
        raise FileNotFoundError(f"文件 {in_filename} 不存在")

    if os.path.isdir(out_filename):
        raise RuntimeError(f"同名文件夹已存在，无法新建文件 {out_filename}")

    if os.path.isfile(out_filename):
        if locale.getdefaultlocale()[0] == "zh_CN":
            backup_filename = "[备份] " + out_filename
        else:
            backup_filename = out_filename + ".bak"
        try:
            shutil.move(out_filename, backup_filename)
        except PermissionError:
            raise RuntimeError(
                f"备份 Excel 文档时发生权限错误，有可能是 Excel 文档已经被其他程序占用，"
                f"有可能是 {out_filename} 已经被 Excel 打开"
            )
        print(f"{out_filename} 同名文件已存在，备份至 {backup_filename}")


def check_update() -> None:
    print("获取最新分发版本号......")
    # TODO Handle the case when the lastest release's tag name is not semantic
    # version.
    try:
        latest_version = get_latest_release_version(REPO_OWNER, REPO_NAME)
    except:
        print("获取最新分发版本号的时候发生错误，暂时跳过。可以通过 --update 命令来手动触发更新检查")
        return
    if parse_version_number(latest_version) > parse_version_number(__version__):
        print(f"检测到更新版本 {latest_version}，请手动更新")
        exit()
    else:
        print("当前已是最新版本")


def net_value_date_is_latest(raw_date: str) -> bool:
    # Take advantage of the knowledge that fund info stays the same
    # within 0:00 to 20:00.

    # WARNING: it's true that most of time the market is not opened
    # in weekends. But we can't use this knowledge in our logic. Because
    # sometimes holiday policy will make this irregular. We had better
    # fall back to use the most robust way to check.

    net_value_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    now_time = datetime.now().time()
    today = date.today()
    yesterday = today - timedelta(days=1)
    if time.min <= now_time < time(20):
        return net_value_date == yesterday
    else:
        return net_value_date == today


def estimate_datetime_is_latest(raw_datetime: str) -> bool:
    # Take advantage of the knowledge that estimate info stays the same
    # within 15:00 to next day 15:00.

    # WARNING: it's true that most of time the market is not opened
    # in weekends. But we can't use this knowledge in our logic. Because
    # sometimes holiday policy will make this irregular. We had better
    # fall back to use the most robust way to check.

    estimate_datetime = datetime.strptime(raw_datetime, "%Y-%m-%d %H:%M")

    open_market_time = time(9, 30)
    close_market_time = time(15)
    now_time = datetime.now().time()
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_close_market_datetime = datetime.combine(today, close_market_time)
    yesterday_close_market_datetime = datetime.combine(yesterday, close_market_time)

    if open_market_time <= now_time <= close_market_time:
        return False
    elif time.min <= now_time < open_market_time:
        return estimate_datetime == yesterday_close_market_datetime
    elif close_market_time < now_time <= time.max:
        return estimate_datetime == today_close_market_datetime
    else:
        raise RuntimeError("Unreachable")


def get_fund_infos(fund_codes: List[str]) -> List[Dict[str, str]]:
    if not os.path.isdir(PERSISTENT_CACHE_DB_DIRECTORY):
        os.makedirs(PERSISTENT_CACHE_DB_DIRECTORY)

    shelf_path = os.path.join(
        PERSISTENT_CACHE_DB_DIRECTORY, PERSISTENT_CACHE_DB_FILE_BASENAME
    )

    with shelve.open(shelf_path) as fund_info_cache_db:
        renewed_variable_access_lock = threading.Lock()
        renewed = {}

        @lru_cache(maxsize=None)
        def get_fund_info(fund_code: str) -> Dict[str, str]:
            need_renew = False
            fund_info = fund_info_cache_db.get(fund_code, {})

            net_value_date = fund_info.get("净值日期")
            if not net_value_date or not net_value_date_is_latest(net_value_date):
                need_renew = True
                fund_info.update(fetch_net_value(fund_code))

            estiamte_datetime = fund_info.get("估算日期")
            if not estiamte_datetime or not estimate_datetime_is_latest(
                estiamte_datetime
            ):
                need_renew = True
                fund_info.update(fetch_estimate(fund_code))

            if need_renew:
                # TIPS: Uncomment following line to profile lock congestion.
                # print(renewed_variable_access_lock.locked())
                renewed_variable_access_lock.acquire()
                renewed[fund_code] = fund_info
                renewed_variable_access_lock.release()

            return fund_info

        # TODO experiment to find a suitable number as threshold between sync and
        # async code
        if len(fund_codes) < 3:
            fund_infos = [get_fund_info(code) for code in tqdm(fund_codes)]
        else:
            with ThreadPoolExecutor() as executor:
                async_mapped = executor.map(get_fund_info, fund_codes)
                fund_infos = list(tqdm(async_mapped, total=len(fund_codes)))  # type: ignore

        print("将基金相关信息写入数据库，留备下次使用，加速下次查询......")
        fund_info_cache_db.update(renewed)

        print("更新缓存 LRU 信息......")
        # Instead of directly in-place updating the "lru_record" entry in
        # fund_info_cache_db, we copy it to a new variable and update the
        # new variable and then copy back. This is because directly in-place
        # updating shelve dict entry requires opening shelve with the `writeback`
        # parameter set to True, which could lead to increased memory cost
        # and IO cost and slow down the program.
        lru = fund_info_cache_db.get("lru_record", LRU())
        for fund_code in fund_codes:
            lru.update(fund_code)
        if len(lru) > PERSISTENT_CACHE_DB_RECORD_MAX_NUM:
            print("检测到缓存较大，清理缓存......")
            to_evict_num = PERSISTENT_CACHE_DB_RECORD_MAX_NUM - len(lru)
            for _ in trange(to_evict_num):
                evicted_fund_code = lru.evict()
                del fund_info_cache_db[evicted_fund_code]
        fund_info_cache_db["lru_record"] = lru

        return fund_infos

        # TODO remove out-dated cache entries


@click.command()
@click.argument("filename")
@click.option("-o", "--output", default="基金信息.xlsx")
@click.option("--disable-update-check", is_flag=True, default=False)
# TODO: @click.option("--update")
@click.version_option(version=__version__)
def main(filename: str, output: str, disable_update_check: bool) -> None:
    # atexit.register(lambda _: input("Press ENTER to exit"))
    atexit.register(lambda: input("按下回车键以退出"))

    # TODO Remove update check logic after switching architecture to
    if not disable_update_check:
        print("检查更新......")
        check_update()

    in_filename = filename
    out_filename = output

    print("检查参数......")
    check_args(in_filename, out_filename)

    print("获取基金代码列表......")
    fund_codes = Path(in_filename).read_text(encoding="utf-8").splitlines()

    print("清洗基金代码列表......")
    fund_codes = [code for code in tqdm(fund_codes) if re.fullmatch(r"\d{6}", code)]
    if not fund_codes:
        print("没有发现基金代码")
        exit()

    print("获取基金相关信息......")
    fund_infos = get_fund_infos(fund_codes)

    print("将基金相关信息写入 Excel 文件......")
    write_to_xlsx(fund_infos, out_filename)

    # The emoji takes inspiration from the black (https://github.com/psf/black)
    print("完满结束! ✨ 🍰 ✨")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
