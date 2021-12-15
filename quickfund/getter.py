import asyncio
import pickle
import shelve
from collections.abc import Iterable
from contextlib import nullcontext
from pathlib import Path
from shelve import Shelf
from typing import cast

from platformdirs import user_cache_dir

from .__version__ import __version__
from .fetcher import FundInfoFetcher
from .models import FundEstimateInfo, FundIARBCInfo, FundInfo, FundNetValueInfo
from .utils.tqdm import tqdm_asyncio


__all__ = ["get_fund_infos"]


PERSISTENT_CACHE_DIR = Path(
    user_cache_dir(appname="QuickFund", appauthor="MapleCCC", version=__version__)
)
PERSISTENT_CACHE_DIR.mkdir(parents=True, exist_ok=True)


async def update_estimate_info(
    fund_code: str, fund_info_db: Shelf[FundInfo], fund_info_fetcher: FundInfoFetcher
) -> None:
    if not FundEstimateInfo.is_latest(fund_info_db[fund_code]):
        estimate_info = await fund_info_fetcher.fetch_estimate(fund_code)
        fund_info_db[fund_code].replace(estimate_info=estimate_info)


async def update_net_value_info(
    fund_code: str, fund_info_db: Shelf[FundInfo], fund_info_fetcher: FundInfoFetcher
) -> None:
    if not FundNetValueInfo.is_latest(fund_info_db[fund_code]):
        net_value_info = await fund_info_fetcher.fetch_net_value(fund_code)
        fund_info_db[fund_code].replace(net_value_info=net_value_info)


async def update_IARBC_info(
    fund_code: str, fund_info_db: Shelf[FundInfo], fund_info_fetcher: FundInfoFetcher
) -> None:
    if not FundIARBCInfo.is_latest(fund_info_db[fund_code]):
        IARBC_info = await fund_info_fetcher.fetch_IARBC(fund_code)
        fund_info_db[fund_code].replace(IARBC_info=IARBC_info)


# TODO use a database library that supports multiple concurrent read/write
# TODO use a database library that supports asynchronous non-blocking write
async def update_fund_info(
    fund_code: str, fund_info_db: Shelf[FundInfo], fund_info_fetcher: FundInfoFetcher
) -> None:

    if fund_code in fund_info_db:
        await update_net_value_info(fund_code, fund_info_db, fund_info_fetcher)
        await update_estimate_info(fund_code, fund_info_db, fund_info_fetcher)
        await update_IARBC_info(fund_code, fund_info_db, fund_info_fetcher)
    else:
        fund_info = await fund_info_fetcher.fetch(fund_code)
        fund_info_db[fund_code] = fund_info


def update_fund_infos(fund_codes: Iterable[str], fund_info_db: Shelf[FundInfo]) -> None:
    fund_info_fetcher = FundInfoFetcher()
    tasks = (
        update_fund_info(fund_code, fund_info_db, fund_info_fetcher)
        for fund_code in set(fund_codes)
    )
    asyncio.run(tqdm_asyncio.gather(*tasks, unit="个", desc="获取基金信息"))


def check_db_version(fund_info_db: Shelf[FundInfo]) -> None:
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
        null_shelf = cast(Shelf[FundInfo], {})
        cm = nullcontext(enter_result=null_shelf)
    else:
        shelve_config = {"protocol": pickle.HIGHEST_PROTOCOL, "writeback": True}
        cm = cast(
            Shelf[FundInfo], shelve.open(str(FUND_INFO_CACHE_DB_PATH), **shelve_config)
        )

    with cm as fund_info_db:

        check_db_version(fund_info_db)

        update_fund_infos(fund_codes, fund_info_db)

        return [fund_info_db[fund_code] for fund_code in fund_codes]
