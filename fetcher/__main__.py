#!/usr/bin/env python3

import atexit
import locale
import os
import re
import shelve
import shutil
import sys
import threading
import traceback
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from itertools import filterfalse
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import attr
import click
import colorama
import semver
import xlsxwriter

from .__version__ import __version__
from .config import REPO_NAME, REPO_OWNER
from .fetcher import fetch_estimate, fetch_net_value
from .github_utils import get_latest_release_version
from .lru import LRU
from .schema import FundInfo
from .tqdm_enhanced import tenumerate, thread_map, tmap, tqdm, trange
from .utils import Logger, bright_blue, print_traceback_digest

# GUI feature of tqdm is experimental. And our application is too fast for the plot to render.
# from tqdm.gui import tqdm, trange


if locale.getdefaultlocale()[0] == "zh_CN":
    PERSISTENT_CACHE_DB_DIRECTORY = ".缓存"
else:
    PERSISTENT_CACHE_DB_DIRECTORY = ".cache"
# Instead of using full filename, we use basename, because shelve requires so.
PERSISTENT_CACHE_DB_FILE_BASENAME = "cache"
PERSISTENT_CACHE_DB_RECORD_MAX_NUM = 2000

ERR_LOG_FILE = "错误日志.txt"

logger = Logger()


def write_to_xlsx(fund_infos: List[FundInfo], xlsx_filename: str) -> None:
    """
    Structuralize a list of fund infos to an Excel document.

    Input: a list of fund infos, and an Excel filename.
    """

    try:
        # TODO profile to see whether and how much setting constant_memory improves
        # performance.
        with xlsxwriter.Workbook(xlsx_filename, {"constant_memory": True}) as workbook:

            logger.log("新建 Excel 文档......")
            worksheet = workbook.add_worksheet()

            # Widen column
            for i, field in enumerate(attr.fields(FundInfo)):
                width = field.metadata.get("width")
                # FIXME Despite the xlsxwriter doc saying that set_column(i, i, None) doesn't
                # change the column width, some simple tests show that it does. The source
                # code of xlsxwriter is too complex that I can't figure out where the
                # bug originates.
                worksheet.set_column(i, i, width)

            # Write header
            logger.log("写入文档头......")
            for i, field in enumerate(attr.fields(FundInfo)):
                header_format = workbook.add_format(
                    {"bold": True, "align": "center", "valign": "top", "border": 1}
                )
                worksheet.write_string(0, i, field.name, header_format)

            # Write body
            logger.log("写入文档体......")
            for row, info in tenumerate(fund_infos, start=1, unit="行", desc="写入基金信息"):
                for col, field in enumerate(attr.fields(FundInfo)):
                    # Judging from source code of xlsxwriter, add_format(None) is
                    # equivalent to default format.
                    cell_format = workbook.add_format(field.metadata.get("format"))
                    worksheet.write(row, col, info[col], cell_format)

            logger.log("Flush 到硬盘......")

    except Exception as exc:
        raise RuntimeError(f"获取基金信息并写入 Excel 文档的时候发生错误") from exc


def check_args(in_filenames: Iterable[str], out_filename: str) -> None:
    """
    Check validness of command line arguments
    """

    # Check in_filenames
    for f in in_filenames:
        if not os.path.exists(f):
            raise FileNotFoundError(f"文件 {f} 不存在")

    # Check out_filename
    if os.path.isdir(out_filename):
        raise RuntimeError(f'同名文件夹已存在，无法新建文件 "{out_filename}"')

    if os.path.isfile(out_filename):
        # If out_filename already exists, make a backup.

        if locale.getdefaultlocale()[0] == "zh_CN":
            backup_filename = "[备份] " + out_filename
        else:
            backup_filename = out_filename + ".bak"

        try:
            shutil.move(out_filename, backup_filename)
        except PermissionError:
            raise RuntimeError(
                f"备份 Excel 文档时发生权限错误，有可能是 Excel 文档已经被其他程序占用，"
                f'有可能是 "{out_filename}" 已经被 Excel 打开，'
                "请关闭文件之后重试"
            ) from None
        logger.log(f'"{out_filename}" 同名文件已存在，备份至 "{backup_filename}"')


def check_update() -> None:
    """
    Check if update to the program is available.
    """

    logger.log("获取最新分发版本号......")
    # TODO Handle the case when the latest release's tag name is not semantic
    # version.
    # TODO Handle the case when the latest release's tag name is semantic version but
    # with additional suffix, like rc (release candidate), build, etc.
    try:
        latest_version = get_latest_release_version(REPO_OWNER, REPO_NAME)
    except:
        logger.log("获取最新分发版本号的时候发生错误，暂时跳过。可以通过 --update 命令来手动触发更新检查")
        return

    if semver.compare(latest_version, __version__) > 0:
        logger.log(f"检测到更新版本 {latest_version}，请手动更新")
        sys.exit()
    else:
        logger.log("当前已是最新版本")


def net_value_date_is_latest(net_value_date: date) -> bool:
    """
    Check if the net value date is latest.

    Take advantage of the knowledge that fund info stays the same
    within 0:00 to 20:00.

    WARNING: it's true that most of time the market is not opened
    in weekends. But we can't use this knowledge in our logic. Because
    sometimes holiday policy will make this irregular. We'd better
    fall back to use the most robust way to check.
    """

    now_time = datetime.now().time()
    today = date.today()
    yesterday = today - timedelta(days=1)

    if time.min <= now_time < time(20):
        return net_value_date == yesterday
    else:
        return net_value_date == today


def estimate_datetime_is_latest(estimate_datetime: datetime) -> bool:
    """
    Check if the estimte datetime is latest.

    Take advantage of the knowledge that estimate info stays the same
    within 15:00 to next day 15:00.

    WARNING: it's true that most of time the market is not opened
    in weekends. But we can't use this knowledge in our logic. Because
    sometimes holiday policy will make this irregular. We'd better
    fall back to use the most robust way to check.
    """

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
    """
    Input: a list of fund codes
    Output: a list of fund infos corresponding to the fund code
    """

    if not os.path.isdir(PERSISTENT_CACHE_DB_DIRECTORY):
        os.makedirs(PERSISTENT_CACHE_DB_DIRECTORY)

    shelf_path = os.path.join(
        PERSISTENT_CACHE_DB_DIRECTORY, PERSISTENT_CACHE_DB_FILE_BASENAME
    )

    with shelve.open(shelf_path) as fund_info_cache_db:
        # Check protocol version
        cache_db_protocol_version = fund_info_cache_db.get("protocol_version")
        if cache_db_protocol_version is None or cache_db_protocol_version < __version__:
            logger.log("缓存数据库的协议版本过低或信息缺失，更新到新版本，并清空旧协议存储......")
            fund_info_cache_db.clear()

        fund_info_cache_db["protocol_version"] = __version__

        # Create variable `new_records` to keep track of the fund infos that get refreshed.
        new_records_access_lock = threading.Lock()
        new_records: Dict[str, FundInfo] = {}

        def add_to_new_records(fund_code: str, fund_info: FundInfo) -> None:
            # TIPS: Uncomment following line to profile lock congestion.
            # print(renewed_variable_access_lock.locked())
            new_records_access_lock.acquire()
            new_records[fund_code] = fund_info
            new_records_access_lock.release()

        @lru_cache(maxsize=None)
        def get_fund_info(fund_code: str) -> FundInfo:
            """
            Input: a fund code
            Output: fund info related to the fund code
            """

            need_renew = False
            fund_info: FundInfo = fund_info_cache_db.get(fund_code, FundInfo())

            net_value_date = fund_info.净值日期
            if net_value_date is None or not net_value_date_is_latest(net_value_date):
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
            if estimate_datetime is None or not estimate_datetime_is_latest(
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
                add_to_new_records(fund_code, fund_info)

            return fund_info

        # FIXME experiment to find a suitable number as threshold between sync and
        # async code
        if len(fund_codes) < 3:
            fund_infos = list(tmap(get_fund_info, fund_codes, unit="个", desc="获取基金信息"))
        else:
            fund_infos = list(
                thread_map(get_fund_info, fund_codes, unit="个", desc="获取基金信息")
            )

        logger.log("将基金相关信息写入数据库，留备下次使用，加速下次查询......")
        fund_info_cache_db.update(new_records)

        logger.log("更新缓存 LRU 信息......")

        # TODO remove out-dated cache entries

        # Instead of directly in-place updating the "lru_record" entry in
        # fund_info_cache_db, we copy it to a new variable and update the
        # new variable and then copy back. This is because directly in-place
        # updating shelve dict entry requires opening shelve with the `writeback`
        # parameter set to True, which could lead to increased memory cost
        # and IO cost, hence slowing down the program.

        lru = fund_info_cache_db.get("lru_record", LRU())
        lru.batch_update(fund_codes)

        if lru.size > PERSISTENT_CACHE_DB_RECORD_MAX_NUM:
            logger.log("检测到缓存较大，清理缓存......")
            to_evict_num = PERSISTENT_CACHE_DB_RECORD_MAX_NUM - len(lru)
            for _ in trange(to_evict_num, unit="条", desc="清理缓存"):
                del fund_info_cache_db[lru.evict()]

        fund_info_cache_db["lru_record"] = lru

        return fund_infos


def validate_fund_code(s: str) -> bool:
    """ Check if a string represents a valid fund code """
    return bool(re.fullmatch(r"[0-9]{6}", s))


@click.command(
    name="fund-info-fetcher",
    help="A script to fetch various fund information from https://fund.eastmoney.com, and structuralize into Excel document",
    epilog="Input file format: one fund code per line.",
    no_args_is_help=True,  # type: ignore
)
@click.argument(
    "fund_codes_or_files",
    nargs=-1,
    metavar="<fund codes or files containing fund codes>",
)
@click.option(
    "-o",
    "--output",
    default="基金信息.xlsx",
    show_default=True,
    help="The output file path.",
)
@click.option("--disable-update-check", is_flag=True, help="Disable update check.")
# @click.option("--disable-cache", is_flag=True)
# @click.option("--versbose", is_flag=True)
# TODO: @click.option("--update")
@click.version_option(version=__version__)
def main(
    fund_codes_or_files: Tuple[str], output: str, disable_update_check: bool
) -> None:
    """ Command line entry function """

    colorama.init()

    @atexit.register
    def pause_wait_enter() -> None:
        if locale.getdefaultlocale()[0] == "zh_CN":
            # localization for Simplified Chinese
            msg = "按回车键以退出"
        else:
            # default to English
            msg = "Press ENTER to exit"
        # WARNING: colorama doesn't seem to be compatible with the builtin input()
        # function under some console environment. The workaround here is to transform
        # from `input("xxx")` to `print("xxx"); input()`.
        print(bright_blue(msg), end="")
        input()

    try:
        # TODO Remove update check logic after switching architecture to
        # server/client model
        if not disable_update_check:
            print("检查更新......")
            check_update()

        if not fund_codes_or_files:
            # FIXME
            print("Usage: fund-info-fetch <list of fund codes>")
            sys.exit()

        in_filenames = filterfalse(validate_fund_code, fund_codes_or_files)
        out_filename = output

        logger.log("检查参数......")
        check_args(in_filenames, out_filename)

        logger.log("获取基金代码列表......")
        fund_codes = []
        for x in fund_codes_or_files:
            if validate_fund_code(x):
                # if x is fund code
                fund_codes.append(x)
            else:
                # if x is filename
                lines = Path(x).read_text(encoding="utf-8").splitlines()
                cleaned_lines = map(str.strip, lines)
                fund_codes.extend(filter(validate_fund_code, cleaned_lines))

        if not fund_codes:
            logger.log("没有发现基金代码")
            sys.exit()

        logger.log("获取基金相关信息......")
        fund_infos = get_fund_infos(fund_codes)

        logger.log("将基金相关信息写入 Excel 文件......")
        write_to_xlsx(fund_infos, out_filename)

        # The emoji takes inspiration from the black (https://github.com/psf/black)
        logger.log("完满结束! ✨ 🍰 ✨")

    except Exception:
        logger.log("Oops! 程序运行过程中遇到了错误，打印错误信息摘要如下：")
        print_traceback_digest()

        with open(ERR_LOG_FILE, "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        logger.log(f'详细错误信息已写入日志文件 "{ERR_LOG_FILE}"，请将日志文件提交给开发者进行调试 debug')


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
