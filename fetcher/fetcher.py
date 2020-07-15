import json
import random
import re
import string
from datetime import datetime
from typing import Dict, List, Union

import requests
from lxml import etree  # type: ignore
from more_itertools import replace

from .schema import FundInfo

__all__ = ["fetch_net_value", "fetch_estimate", "fetch_fund_info"]


def fetch_net_value(fund_code: str) -> FundInfo:
    try:
        # Add random parameter to the URL to break any cache mechanism of
        # the server or the network or the requests library.
        salt = "".join(random.sample(string.ascii_lowercase, 10))
        params: Dict[str, Union[str, int]] = {
            "type": "lsjz",
            "page": 1,
            "per": 2,
            "code": fund_code,
            "salt": salt,
        }
        net_value_api = "https://fund.eastmoney.com/f10/F10DataApi.aspx"
        response = requests.get(net_value_api, params=params)
        response.raise_for_status()

        response.encoding = "utf-8"
        text = response.text
        # Relax the regular expression to be more permissive and hence
        # more robust to ill input. Remember, we are dealing with data
        # coming from stranger environment. Better not depend on some
        # strong assumption made about them.
        content = re.match(
            r"var\s*apidata\s*=\s*{\s*content\s*:\s*\"(?P<content>.*)\"", text
        ).group("content")

        root = etree.XML(content)
        keys = root.xpath("/table/thead/tr[1]/th/text()")
        # WARNING: don't use root.xpath("/table/tbody/tr//td/text()") to extract
        # values. The XPath expression will omit empty text, causing erroneous
        # result
        tds = root.xpath("/table/tbody/tr[1]/td")
        values: List[str] = [td.text for td in tds]
        values = list(replace(values, lambda x: x is None, [""]))

        if len(keys) != len(values):
            raise RuntimeError("解析基金信息时键值对不匹配")

        responded_data = dict(zip(keys, values))

        fund_info = FundInfo()
        fund_info.基金代码 = fund_code
        fund_info.净值日期 = datetime.strptime(responded_data["净值日期"], "%Y-%m-%d").date()
        fund_info.单位净值 = float(responded_data["单位净值"])
        fund_info.日增长率 = float(responded_data["日增长率"].rstrip("% ")) * 0.01
        fund_info.分红送配 = responded_data["分红送配"]

        last_time_tds = root.xpath("/table/tbody/tr[2]/td")
        last_time_values = [td.text for td in last_time_tds]
        last_time_values = list(replace(last_time_values, lambda x: x is None, [""]))

        if len(keys) != len(values):
            raise RuntimeError("解析基金信息时键值对不匹配")

        last_time_info = dict(zip(keys, last_time_values))

        fund_info.上一天净值 = float(last_time_info["单位净值"])
        fund_info.上一天净值日期 = datetime.strptime(last_time_info["净值日期"], "%Y-%m-%d").date()

        return fund_info
    except Exception as exc:
        raise RuntimeError(f"获取基金代码为 {fund_code} 的基金相关净值信息时发生错误") from exc


def fetch_estimate(fund_code: str) -> FundInfo:
    try:
        # Add random parameter to the URL to break potential cache mechanism of
        # the server or the network or the requests library.
        salt = "".join(random.sample(string.ascii_lowercase, 10))
        params = {"salt": salt}
        estimate_api = "http://fundgz.1234567.com.cn/js/{fund_code}.js"
        response = requests.get(estimate_api.format(fund_code=fund_code), params=params)
        response.raise_for_status()

        response.encoding = "utf-8"
        text = response.text
        # Relax the regular expression to be more permissive and hence
        # more robust to ill input. Remember, we are dealing with data
        # coming from stranger environment. Better not depend on some
        # strong assumption made about them.
        content = re.match(r"jsonpgz\s*\((?P<content>.*)\)\s*;", text).group("content")
        json_data = json.loads(content)

        fund_info = FundInfo()
        if fund_code != json_data["fundcode"]:
            raise RuntimeError(f"爬取基金代码为 {fund_code} 的基金相关估算信息时发现基金代码不匹配")
        fund_info.基金代码 = fund_code
        fund_info.基金名称 = json_data["name"]
        fund_info.估算日期 = datetime.strptime(json_data["gztime"], "%Y-%m-%d %H:%M")
        fund_info.实时估值 = float(json_data["gsz"])
        # WARN: the estimate_growth_rate from API is itself a percentage number (despite
        # that it doesn't come with a % mark), so we need to multiply it by 0.01.
        estimate_growth_rate = json_data["gszzl"]
        # FIXME what's the range of 估算增长率? Can we give it a bound and use the
        # bound to conduct sanity check?
        # if not (0 <= estimate_growth_rate <= 1):
        #     raise NotImplementedError
        fund_info.估算增长率 = float(estimate_growth_rate) * 0.01

        return fund_info
    except Exception as exc:
        raise RuntimeError(f"获取基金代码为 {fund_code} 的基金相关估算信息时发生错误") from exc


def fetch_fund_info(fund_code: str) -> FundInfo:
    try:
        fund_info = FundInfo()
        net_value_info = fetch_net_value(fund_code)
        fund_info.基金代码 = net_value_info.基金代码
        fund_info.净值日期 = net_value_info.净值日期
        fund_info.单位净值 = net_value_info.单位净值
        fund_info.日增长率 = net_value_info.日增长率
        fund_info.分红送配 = net_value_info.分红送配
        fund_info.上一天净值 = net_value_info.上一天净值
        fund_info.上一天净值日期 = net_value_info.上一天净值日期

        estimate_data = fetch_estimate(fund_code)
        fund_info.基金代码 = estimate_data.基金代码
        fund_info.基金名称 = estimate_data.基金名称
        fund_info.估算日期 = estimate_data.估算日期
        fund_info.实时估值 = estimate_data.实时估值
        fund_info.估算增长率 = estimate_data.估算增长率

        return fund_info
    except Exception as exc:
        raise RuntimeError(f"获取基金代码为 {fund_code} 的基金相关信息时发生错误") from exc


if __name__ == "__main__":
    print(fetch_net_value("000478"))
