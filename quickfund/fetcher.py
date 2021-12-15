import asyncio
import json
import random
import string
from datetime import date, datetime
from typing import cast

import aiohttp
import pandas
import regex
from aiohttp import ClientSession
from aiohttp_retry import ListRetry, RetryClient
from lxml import etree
from more_itertools import one

from .models import FundEstimateInfo, FundIARBCInfo, FundInfo, FundNetValueInfo
from .utils import on_failure_raises


__all__ = ["FundInfoFetcher"]


class FundInfoFetcher:
    """
    A fetcher that handles fetching fund infos.

    A `FundInfoFetcher` must be created and used inside of an event loop. Creating or
    using a `FundInfoFetcher` outside of an event loop is forbidden. Specifically, a
    fetcher's life-cycle should be shorter than the life-cyle of the event loop within
    which it is created.

    Ref: https://docs.aiohttp.org/en/stable/faq.html#why-is-creating-a-clientsession-outside-of-an-event-loop-dangerous
    Quote: "Why is creating a ClientSession outside of an event loop dangerous? Short answer is: life-cycle of all asyncio objects should be shorter than life-cycle of event loop."
    """

    def __init__(self) -> None:

        # Restrict the size of the connection pool for scraping ethic
        conn = aiohttp.TCPConnector(limit_per_host=30)
        retry_options = ListRetry(
            timeouts=[0, 0, 0.6, 1.2], statuses={500, 502, 503, 504, 514}
        )
        retry_client = RetryClient(connector=conn, retry_options=retry_options)

        # TODO we should inform the type checker that RetryClient has the same interface
        # with that of ClientSession. We can either do it nominally by making
        # RetryClient a subclass of ClientSession, or do it structurally by duck typing
        # / structural typing / typing.Protocol, etc.
        self._session: ClientSession = cast(ClientSession, retry_client)

    __slots__ = ["_session"]

    async def get_net_value_api_response_text(self, fund_code: str) -> str:

        # Add random parameter to the URL to break any cache mechanism of
        # the server or the network or the aiohttp library.
        salt_key = "锟斤铐"
        # TODO can we just use random bytes as salt_value?
        salt_value = "".join(random.choices(string.hexdigits, k=10))

        net_value_api = "https://fund.eastmoney.com/f10/F10DataApi.aspx"
        params = {
            "type": "lsjz",  # 历史净值
            "page": 1,
            "per": 2,
            "code": fund_code,
            salt_key: salt_value,
        }

        async with self._session.get(net_value_api, params=params) as response:
            response.raise_for_status()
            return await response.text(encoding="utf-8")

    def parse_net_value_api_response_text(self, text: str) -> pandas.DataFrame:

        # TODO pandas.read_html accept url as argument, we can definitely use this feature
        # to simplify the code, if it ever supports async/await syntax in the future.
        # pandas.read_html uses urllib.request.urlopen under the hood and feeds it to etree.html.parse()

        # TODO configure pandas.read_html to use the most performant parser backend

        # TODO wait for upstream PR to land https://github.com/microsoft/python-type-stubs/pull/85

        dfs = pandas.read_html(text, parse_dates=["净值日期"], keep_default_na=False)
        return one(dfs)

    def pack_to_FundNetValueInfo(self, data: pandas.DataFrame) -> FundNetValueInfo:
        net_value_info = FundNetValueInfo(
            净值日期=data.净值日期[0].date(),
            单位净值=data.单位净值[0],
            日增长率=float(data.日增长率[0].rstrip("% ")) * 0.01,
            分红送配=data.分红送配[0],
            上一天净值=data.单位净值[1],
            上一天净值日期=data.净值日期[1].date(),
        )  # type: ignore # FIXME https://github.com/python-attrs/attrs/issues/795

        return net_value_info

    @on_failure_raises(RuntimeError, "获取基金代码为 {fund_code} 的基金相关净值信息时发生错误")
    async def fetch_net_value(self, fund_code: str) -> FundNetValueInfo:
        """Fetch the net value related info related to the given fund code"""

        text = await self.get_net_value_api_response_text(fund_code)
        data = self.parse_net_value_api_response_text(text)
        net_value_info = self.pack_to_FundNetValueInfo(data)

        return net_value_info

    async def get_estimate_api_response_text(self, fund_code: str) -> str:

        # Add random parameter to the URL to break potential cache mechanism of
        # the server or the network or the aiohttp library.
        salt_key = "锟斤铐"
        salt_value = "".join(random.choices(string.hexdigits, k=10))

        estimate_api = f"https://fundgz.1234567.com.cn/js/{fund_code}.js"
        params = {salt_key: salt_value}

        async with self._session.get(estimate_api, params=params) as response:
            response.raise_for_status()
            return await response.text(encoding="utf-8")

    def parse_estimate_api_response_text(self, text: str) -> dict[str, str]:

        # TODO it would greatly simplify the code if json.loads has the same level of input
        # tolerance with that of pandas.read_html

        # TODO relax the regular expression to be more permissive and
        # hence more robust to ill input. Remember, we are dealing with
        # data coming from stranger environment. Better not depend on
        # some strong assumption made about them.

        # TODO the most rubost approach is to use a JavaScript parser to parse the text
        # argument.

        pattern = r"jsonpgz\((?P<json>.*)\);"
        m = regex.fullmatch(pattern, text)

        if not m:
            raise ValueError(
                f'regex pattern "{pattern}" doesn\'t match estimate API response text "{text}"'
            )

        json_text = m.group("json")
        return json.loads(json_text)

    def pack_to_FundEstimateInfo(self, data: dict[str, str]) -> FundEstimateInfo:
        estimate_info = FundEstimateInfo(
            基金代码=data["fundcode"],
            基金名称=data["name"],
            估算日期=datetime.strptime(data["gztime"], "%Y-%m-%d %H:%M"),
            实时估值=float(data["gsz"]),
            # The estimate growth rate from API is itself a percentage number (despite
            # that it doesn't come with a % mark), so we need to multiply it by 0.01.
            估算增长率=float(data["gszzl"]) * 0.01,
        )  # type: ignore # FIXME https://github.com/python-attrs/attrs/issues/795

        # TODO what's the range of 估算增长率? Can we give it a bound and use the
        # bound to conduct sanity check?
        # if not (0 <= estimate_growth_rate <= 1):
        #     raise NotImplementedError

        return estimate_info

    @on_failure_raises(RuntimeError, "获取基金代码为 {fund_code} 的基金相关估算信息时发生错误")
    async def fetch_estimate(self, fund_code: str) -> FundEstimateInfo:
        """Fetch the estimate info related to the given fund code"""

        text = await self.get_estimate_api_response_text(fund_code)
        data = self.parse_estimate_api_response_text(text)
        estimate_info = self.pack_to_FundEstimateInfo(data)

        assert data["fundcode"] == fund_code, f"爬取基金代码为 {fund_code} 的基金相关估算信息时发现基金代码不匹配"

        return estimate_info

    async def get_fund_info_page_text(self, fund_code: str) -> str:

        # Add random parameter to the URL to break potential cache mechanism of
        # the server or the network or the aiohttp library.
        salt_key = "锟斤铐"
        salt_value = "".join(random.choices(string.hexdigits, k=10))

        fund_info_page_url = f"https://fund.eastmoney.com/{fund_code}.html"
        params = {salt_key: salt_value}

        async with self._session.get(fund_info_page_url, params=params) as response:
            response.raise_for_status()
            return await response.text(encoding="utf-8")

    def parse_fund_info_page_text_and_get_IARBC_data(
        self,
        text: str,
    ) -> tuple[date, pandas.DataFrame]:

        html = etree.HTML(text)
        cutoff_date_str = one(cast(list, html.xpath("//span[@id='jdzfDate']"))).text
        cutoff_date = datetime.strptime(cutoff_date_str, "%Y-%m-%d").date()

        table: str = etree.tostring(
            one(cast(list, html.xpath("//li[@id='increaseAmount_stage']"))),
            encoding=str,
        )
        df = one(pandas.read_html(table, index_col=0))

        return cutoff_date, df

    def pack_to_FundIARBCInfo(
        self, cutoff_date: date, data: pandas.DataFrame
    ) -> FundIARBCInfo:
        def reformat_IARBC(IARBC: str) -> str:
            m = regex.fullmatch(r"(?P<rank>\d+) \| (?P<total>\d+)", IARBC)

            if not m:
                raise ValueError("invalid IARBC format")

            rank, total = m.group("rank", "total")
            return rank + "/" + total

        return FundIARBCInfo(
            同类排名截止日期=cutoff_date,
            近1周同类排名=reformat_IARBC(data.近1周.同类排名),
            近1月同类排名=reformat_IARBC(data.近1月.同类排名),
            近3月同类排名=reformat_IARBC(data.近3月.同类排名),
            近6月同类排名=reformat_IARBC(data.近6月.同类排名),
            今年来同类排名=reformat_IARBC(data.今年来.同类排名),
            近1年同类排名=reformat_IARBC(data.近1年.同类排名),
            近2年同类排名=reformat_IARBC(data.近2年.同类排名),
            近3年同类排名=reformat_IARBC(data.近3年.同类排名),
        )  # type: ignore # FIXME https://github.com/python-attrs/attrs/issues/795

    @on_failure_raises(RuntimeError, "获取基金代码为 {fund_code} 的基金相关同类排名信息时发生错误")
    async def fetch_IARBC(self, fund_code: str) -> FundIARBCInfo:
        """Fetch the IARBC info related to the given fund code"""

        text = await self.get_fund_info_page_text(fund_code)
        cutoff_date, data = self.parse_fund_info_page_text_and_get_IARBC_data(text)
        IARBC_info = self.pack_to_FundIARBCInfo(cutoff_date, data)

        return IARBC_info

    @on_failure_raises(RuntimeError, "获取基金代码为 {fund_code} 的基金相关信息时发生错误")
    async def fetch(self, fund_code: str) -> FundInfo:
        """Fetch the fund info related to the given fund code"""

        net_value_info, estimate_info, IARBC_info = await asyncio.gather(
            self.fetch_net_value(fund_code),
            self.fetch_estimate(fund_code),
            self.fetch_IARBC(fund_code),
        )

        return FundInfo.combine(net_value_info, estimate_info, IARBC_info)


if __name__ == "__main__":
    print(asyncio.run(FundInfoFetcher().fetch("000478")))
