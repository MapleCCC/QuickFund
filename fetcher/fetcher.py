import asyncio
import json
import random
import re
import string
from datetime import date, datetime
from typing import cast

import aiohttp
import pandas
from aiohttp_retry import ListRetry, RetryClient
from lxml import etree
from more_itertools import one

from .models import FundEstimateInfo, FundIARBCInfo, FundInfo, FundNetValueInfo
from .utils import on_failure_raises, register_at_loop_close


__all__ = ["fetch_net_value", "fetch_estimate", "fetch_fund_info"]


def _get_client_session() -> RetryClient:
    """
    "Why is creating a ClientSession outside of an event loop dangerous?
    Short answer is: life-cycle of all asyncio objects should be shorter than life-cycle of event loop."
    https://docs.aiohttp.org/en/stable/faq.html#why-is-creating-a-clientsession-outside-of-an-event-loop-dangerous

    Called inside coroutines
    """

    def graceful_shutdown_client_session(session: RetryClient) -> None:
        # Ref: https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        loop.create_task(session.close())
        loop.create_task(asyncio.sleep(0))

    loop = asyncio.get_running_loop()

    try:
        return loop._aiohttp_client_session

    except AttributeError:

        # Restrict the size of the connection pool for scraping ethic
        conn = aiohttp.TCPConnector(limit_per_host=30)
        retry_options = ListRetry(
            timeouts=[0, 0, 0.6, 1.2], statuses={500, 502, 503, 504, 514}
        )
        session = RetryClient(connector=conn, retry_options=retry_options)

        loop._aiohttp_client_session = session
        register_at_loop_close(loop, lambda: graceful_shutdown_client_session(session))

        return session


async def get_net_value_api_response_text(fund_code: str) -> str:

    # Add random parameter to the URL to break any cache mechanism of
    # the server or the network or the requests library.
    salt_key = "锟斤铐"
    salt_value = "".join(random.choices(string.hexdigits, k=10))

    net_value_api = "https://fund.eastmoney.com/f10/F10DataApi.aspx"
    params = {
        "type": "lsjz",  # 历史净值
        "page": 1,
        "per": 2,
        "code": fund_code,
        salt_key: salt_value,
    }

    session = _get_client_session()
    async with session.get(net_value_api, params=params) as response:
        response.raise_for_status()
        return await response.text(encoding="utf-8")


def parse_net_value_api_response_text(text: str) -> pandas.DataFrame:

    # TODO pandas.read_html accept url as argument, we can definitely use this feature
    # to simplify the code, if it ever supports async/await syntax in the future.

    # TODO configure pandas.read_html to use the most performant parser backend

    dfs = pandas.read_html(text, parse_dates=["净值日期"], keep_default_na=False)
    return one(dfs)


def pack_to_FundNetValueInfo(data: pandas.DataFrame) -> FundNetValueInfo:
    net_value_info = FundNetValueInfo(
        净值日期=data.净值日期[0].date(),
        单位净值=data.单位净值[0],
        日增长率=float(data.日增长率[0].rstrip("% ")) * 0.01,
        分红送配=data.分红送配[0],
        上一天净值=data.单位净值[1],
        上一天净值日期=data.净值日期[1].date(),
    )  # type: ignore # https://github.com/python-attrs/attrs/issues/795

    return net_value_info


@on_failure_raises(RuntimeError, "获取基金代码为 {fund_code} 的基金相关净值信息时发生错误")
async def fetch_net_value(fund_code: str) -> FundNetValueInfo:
    """Fetch the net value related info related to the given fund code"""

    text = await get_net_value_api_response_text(fund_code)
    data = parse_net_value_api_response_text(text)
    net_value_info = pack_to_FundNetValueInfo(data)

    return net_value_info


async def get_estimate_api_response_text(fund_code: str) -> str:

    # Add random parameter to the URL to break potential cache mechanism of
    # the server or the network or the requests library.
    salt_key = "锟斤铐"
    salt_value = "".join(random.choices(string.hexdigits, k=10))

    estimate_api = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
    params = {salt_key: salt_value}

    session = _get_client_session()
    async with session.get(estimate_api, params=params) as response:
        response.raise_for_status()
        return await response.text(encoding="utf-8")


def parse_estimate_api_response_text(text: str) -> dict[str, str]:

    # TODO it would greatly simplify the code if json.loads has the same level of input
    # tolerance with that of pandas.read_html

    # TODO relax the regular expression to be more permissive and
    # hence more robust to ill input. Remember, we are dealing with
    # data coming from stranger environment. Better not depend on
    # some strong assumption made about them.

    pattern = r"jsonpgz\((?P<json>.*)\);"
    m = re.fullmatch(pattern, text)

    if not m:
        raise ValueError(
            f"regex pattern {pattern} doesn't match estimate API response text {text}"
        )

    json_text = m.group("json")
    return json.loads(json_text)


def pack_to_FundEstimateInfo(data: dict[str, str]) -> FundEstimateInfo:
    estimate_info = FundEstimateInfo(
        基金代码=data["fundcode"],
        基金名称=data["name"],
        估算日期=datetime.strptime(data["gztime"], "%Y-%m-%d %H:%M"),
        实时估值=float(data["gsz"]),
        # The estimate growth rate from API is itself a percentage number (despite
        # that it doesn't come with a % mark), so we need to multiply it by 0.01.
        估算增长率=float(data["gszzl"]) * 0.01,
    )  # type: ignore # https://github.com/python-attrs/attrs/issues/795

    # TODO what's the range of 估算增长率? Can we give it a bound and use the
    # bound to conduct sanity check?
    # if not (0 <= estimate_growth_rate <= 1):
    #     raise NotImplementedError

    return estimate_info


@on_failure_raises(RuntimeError, "获取基金代码为 {fund_code} 的基金相关估算信息时发生错误")
async def fetch_estimate(fund_code: str) -> FundEstimateInfo:
    """Fetch the estimate info related to the given fund code"""

    text = await get_estimate_api_response_text(fund_code)
    data = parse_estimate_api_response_text(text)
    estimate_info = pack_to_FundEstimateInfo(data)

    assert data["fundcode"] == fund_code, f"爬取基金代码为 {fund_code} 的基金相关估算信息时发现基金代码不匹配"

    return estimate_info


async def get_fund_info_page_text(fund_code: str) -> str:

    # Add random parameter to the URL to break potential cache mechanism of
    # the server or the network or the requests library.
    salt_key = "锟斤铐"
    salt_value = "".join(random.choices(string.hexdigits, k=10))

    fund_info_page_url = f"http://fund.eastmoney.com/{fund_code}.html"
    params = {salt_key: salt_value}

    session = _get_client_session()
    async with session.get(fund_info_page_url, params=params) as response:
        response.raise_for_status()
        return await response.text(encoding="utf-8")


def parse_fund_info_page_text_and_get_IARBC_data(
    text: str,
) -> tuple[date, pandas.DataFrame]:

    html = etree.HTML(text)
    cutoff_date_str = one(cast(list, html.xpath("//span[@id='jdzfDate']"))).text
    cutoff_date = datetime.strptime(cutoff_date_str, "%Y-%m-%d").date()

    table: str = etree.tostring(
        one(cast(list, html.xpath("//li[@id='increaseAmount_stage']"))), encoding=str
    )
    df = one(pandas.read_html(table, index_col=0))

    return cutoff_date, df


def pack_to_FundIARBCInfo(cutoff_date: date, data: pandas.DataFrame) -> FundIARBCInfo:
    return FundIARBCInfo(
        同类排名截止日期=cutoff_date,
        近1周同类排名=data.近1周.同类排名,
        近1月同类排名=data.近1月.同类排名,
        近3月同类排名=data.近3月.同类排名,
        近6月同类排名=data.近6月.同类排名,
        今年来同类排名=data.今年来.同类排名,
        近1年同类排名=data.近1年.同类排名,
        近2年同类排名=data.近2年.同类排名,
        近3年同类排名=data.近3年.同类排名,
    )  # type: ignore # https://github.com/python-attrs/attrs/issues/795


async def fetch_IARBC(fund_code: str) -> FundIARBCInfo:

    text = await get_fund_info_page_text(fund_code)
    cutoff_date, data = parse_fund_info_page_text_and_get_IARBC_data(text)
    IARBC_info = pack_to_FundIARBCInfo(cutoff_date, data)

    return IARBC_info


@on_failure_raises(RuntimeError, "获取基金代码为 {fund_code} 的基金相关信息时发生错误")
async def fetch_fund_info(fund_code: str) -> FundInfo:
    """Fetch the fund info related to the given fund code"""

    return FundInfo.combine(
        await fetch_net_value(fund_code),
        await fetch_estimate(fund_code),
        await fetch_IARBC(fund_code),
    )


if __name__ == "__main__":
    print(asyncio.run(fetch_net_value("000478")))
