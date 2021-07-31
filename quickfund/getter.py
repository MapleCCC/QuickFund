import asyncio
import pickle
import shelve
from collections.abc import Iterable
from contextlib import nullcontext
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import cast

from platformdirs import user_cache_dir

from .__version__ import __version__
from .fetcher import fetch_estimate, fetch_fund_info, fetch_IARBC, fetch_net_value
from .models import FundInfo
from .tqdm import tqdm_asyncio
from .typing import Shelf


PERSISTENT_CACHE_DIR = Path(user_cache_dir(appname="QuickFund", appauthor="MapleCCC", version=__version__))


china_timezone = timezone(timedelta(hours=8), name="UTC+8")


def net_value_date_is_latest(net_value_date: date) -> bool:
    """
    Check if the net value date is the latest.

    Take advantage of the knowledge that fund info stays the same
    within 0:00 to 20:00.

    `net_value_date` should be of China timezone.

    Although it usually doesn't open in weekends, the market may irregularly
    open/close subject to holiday policies. We should stick with the most
    robust check.
    """

    china_now = datetime.now(china_timezone)
    now_time = china_now.time()
    today = china_now.date()
    yesterday = today - timedelta(days=1)

    if time.min <= now_time < time(20):
        return net_value_date == yesterday
    else:
        return net_value_date == today


def estimate_datetime_is_latest(estimate_datetime: datetime) -> bool:
    """
    Check if the estimate datetime is the latest.

    Take advantage of the knowledge that estimate info stays the same
    within 15:00 to next day 9:30.

    `estimate_datetime` should be of China timezone.

    Although it usually doesn't open in weekends, the market may irregularly
    open/close subject to holiday policies. We should stick with the most
    robust check.
    """

    market_open_time = time(9, 30)
    market_close_time = time(15)

    china_now = datetime.now(china_timezone)
    now_time = china_now.time()

    today = china_now.date()
    yesterday = today - timedelta(days=1)

    today_market_close_datetime = datetime.combine(today, market_close_time)
    yesterday_market_close_datetime = datetime.combine(yesterday, market_close_time)

    if market_open_time <= now_time <= market_close_time:
        return False
    elif time.min <= now_time < market_open_time:
        return estimate_datetime == yesterday_market_close_datetime
    elif market_close_time < now_time <= time.max:
        return estimate_datetime == today_market_close_datetime
    else:
        raise RuntimeError("Unreachable")


def IARBC_date_is_latest(d: date) -> bool:
    china_now = datetime.now(china_timezone)
    today = china_now.date()
    return d == today


async def update_estimate_info(
    fund_code: str, fund_info_db: Shelf[str, FundInfo]
) -> None:
    estimate_datetime = fund_info_db[fund_code].估算日期
    if not estimate_datetime_is_latest(estimate_datetime):
        estimate_info = await fetch_estimate(fund_code)
        fund_info_db[fund_code].replace(estimate_info=estimate_info)


async def update_net_value_info(
    fund_code: str, fund_info_db: Shelf[str, FundInfo]
) -> None:
    net_value_date = fund_info_db[fund_code].净值日期
    if not net_value_date_is_latest(net_value_date):
        net_value_info = await fetch_net_value(fund_code)
        fund_info_db[fund_code].replace(net_value_info=net_value_info)


async def update_IARBC_info(fund_code: str, fund_info_db: Shelf[str, FundInfo]) -> None:
    IARBC_date = fund_info_db[fund_code].同类排名截止日期
    if not IARBC_date_is_latest(IARBC_date):
        IARBC_info = await fetch_IARBC(fund_code)
        fund_info_db[fund_code].replace(IARBC_info=IARBC_info)


# TODO use a database library that supports multiple concurrent read/write
# TODO use a database library that supports asynchronous non-blocking write
async def update_fund_info(fund_code: str, fund_info_db: Shelf[str, FundInfo]) -> None:

    if fund_code in fund_info_db:
        await update_net_value_info(fund_code, fund_info_db)
        await update_estimate_info(fund_code, fund_info_db)
        await update_IARBC_info(fund_code, fund_info_db)
    else:
        fund_info = await fetch_fund_info(fund_code)
        fund_info_db[fund_code] = fund_info


def update_fund_infos(
    fund_codes: Iterable[str], fund_info_db: Shelf[str, FundInfo]
) -> None:
    tasks = (update_fund_info(fund_code, fund_info_db) for fund_code in set(fund_codes))
    asyncio.run(tqdm_asyncio.gather(*tasks, unit="个", desc="获取基金信息"))


def check_db_version(fund_info_db: Shelf[str, FundInfo]) -> None:
    if fund_info_db.get("version") != __version__:
        # 缓存数据库的版本不一致或版本信息缺失，清空旧存储, 并重置到当前版本
        fund_info_db.clear()
        fund_info_db["version"] = __version__  # type: ignore # we don't trade simplicity of type annotation for a meta edgy case


def get_fund_infos(
    fund_codes: list[str], disable_cache: bool = False
) -> list[FundInfo]:
    """
    Input: a list of fund codes
    Output: a list of fund infos corresponding to the fund codes
    """

    FUND_INFO_CACHE_DB_PATH = PERSISTENT_CACHE_DIR / "fund-infos"

    if disable_cache:
        cm = nullcontext(enter_result={})
    else:
        shelve_config = {"protocol": pickle.HIGHEST_PROTOCOL, "writeback": True}
        cm = shelve.open(str(FUND_INFO_CACHE_DB_PATH), **shelve_config)

    with cm as fund_info_db:

        # Shelf is not a generic type, therefore not friendly to type checker
        # TODO there should be a Pull Request making Shelf a generic type
        fund_info_db = cast(Shelf[str, FundInfo], fund_info_db)

        check_db_version(fund_info_db)

        update_fund_infos(fund_codes, fund_info_db)

        return [fund_info_db[fund_code] for fund_code in fund_codes]
