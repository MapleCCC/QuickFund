#!/usr/bin/env python3

import atexit
import locale
import os
import re
import shelve
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable, Iterator, List, TypeVar

import click
import xlsxwriter
from tqdm import tqdm, trange

from .__version__ import __version__
from .config import REPO_NAME, REPO_OWNER
from .fetcher import fetch_estimate, fetch_net_value
from .github_utils import get_latest_release_version
from .lru import LRU
from .schema import MISSING, FundInfo
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


# TODO refactor write_to_xlsx. Such a long function is prone to error and grows
# harder to maintain.
def write_to_xlsx(fund_infos: List[FundInfo], xlsx_filename: str) -> None:
    try:
        with xlsxwriter.Workbook(xlsx_filename) as workbook:

            print("新建 Excel 文档......")
            worksheet = workbook.add_worksheet()

            # Widen column
            for i, field in enumerate(fields(FundInfo)):
                width = field.metadata.get("width")
                worksheet.set_column(i, i, width)

            # Write header
            print("写入文档头......")
            for i, field in enumerate(fields(FundInfo)):
                header_format = workbook.add_format(
                    {"bold": True, "align": "center", "valign": "top", "border": 1}
                )
                worksheet.write_string(0, i, field.name, header_format)

            # Write body
            print("写入文档体......")
            for row, info in enumerate(tqdm(fund_infos), start=1):
                for col, field in enumerate(fields(FundInfo)):
                    # TODO what happen if we call add_format(None)?
                    cell_format = workbook.add_format(field.metadata.get("format"))
                    worksheet.write(row, col, info[col], cell_format)

            print("Flush 到硬盘......")

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
                f"有可能是 {out_filename} 已经被 Excel 打开，"
                "请关闭文件之后重试"
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


def net_value_date_is_latest(net_value_date: date) -> bool:
    # Take advantage of the knowledge that fund info stays the same
    # within 0:00 to 20:00.

    # WARNING: it's true that most of time the market is not opened
    # in weekends. But we can't use this knowledge in our logic. Because
    # sometimes holiday policy will make this irregular. We had better
    # fall back to use the most robust way to check.

    now_time = datetime.now().time()
    today = date.today()
    yesterday = today - timedelta(days=1)
    if time.min <= now_time < time(20):
        return net_value_date == yesterday
    else:
        return net_value_date == today


def estimate_datetime_is_latest(estimate_datetime: datetime) -> bool:
    # Take advantage of the knowledge that estimate info stays the same
    # within 15:00 to next day 15:00.

    # WARNING: it's true that most of time the market is not opened
    # in weekends. But we can't use this knowledge in our logic. Because
    # sometimes holiday policy will make this irregular. We had better
    # fall back to use the most robust way to check.

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


def get_fund_infos(fund_codes: List[str]) -> List[FundInfo]:
    if not os.path.isdir(PERSISTENT_CACHE_DB_DIRECTORY):
        os.makedirs(PERSISTENT_CACHE_DB_DIRECTORY)

    shelf_path = os.path.join(
        PERSISTENT_CACHE_DB_DIRECTORY, PERSISTENT_CACHE_DB_FILE_BASENAME
    )

    with shelve.open(shelf_path) as fund_info_cache_db:
        renewed_variable_access_lock = threading.Lock()
        renewed = {}

        @lru_cache(maxsize=None)
        def get_fund_info(fund_code: str) -> FundInfo:
            need_renew = False
            fund_info = fund_info_cache_db.get(fund_code, FundInfo())

            net_value_date = fund_info.净值日期
            if net_value_date == MISSING or not net_value_date_is_latest(
                net_value_date
            ):
                need_renew = True
                data = fetch_net_value(fund_code)
                fund_info.基金代码 = data.基金代码
                fund_info.净值日期 = data.净值日期
                fund_info.单位净值 = data.单位净值
                fund_info.日增长率 = data.日增长率
                fund_info.分红送配 = data.分红送配
                fund_info.上一天净值 = data.上一天净值
                fund_info.上一天净值日期 = data.上一天净值日期

            estimate_datetime = fund_info.估算日期
            if estimate_datetime == MISSING or not estimate_datetime_is_latest(
                estimate_datetime
            ):
                need_renew = True
                data = fetch_estimate(fund_code)
                fund_info.基金代码 = data.基金代码
                fund_info.基金名称 = data.基金名称
                fund_info.估算日期 = data.估算日期
                fund_info.实时估值 = data.实时估值
                fund_info.估算增长率 = data.估算增长率

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
                fund_infos = list(tqdm(async_mapped, total=len(fund_codes)))  # type: ignore # nopep8

        print("将基金相关信息写入数据库，留备下次使用，加速下次查询......")
        fund_info_cache_db.update(renewed)

        print("更新缓存 LRU 信息......")

        # TODO remove out-dated cache entries

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
    # server/client model
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
