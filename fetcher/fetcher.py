import json
import random
import re
import string
from typing import Any, Dict, List

import requests
from lxml import etree  # type: ignore
from more_itertools import replace

__all__ = ["fetch_fund_info"]

# Unfortunately current state of lxml type stub is far from complete.
# https://github.com/python/typeshed/issues/525
ETree = Any


def fetch_net_value(fund_code: str) -> Dict[str, str]:
    # Add random parameter to the URL to break any cache mechanism of
    # the server or the network or the requests library.
    garbage = "".join(random.sample(string.ascii_lowercase, 10))
    params = {
        "type": "lsjz",
        "page": 1,
        "per": 2,
        "code": fund_code,
        "garbage": garbage,
    }
    net_value_api = "https://fund.eastmoney.com/f10/F10DataApi.aspx"
    response = requests.get(net_value_api, params=params)
    response.encoding = "utf-8"
    text = response.text
    content = re.match(r"var apidata={ content:\"(?P<content>.*)\"", text).group(
        "content"
    )

    root = etree.XML(content)
    keys = root.xpath("/table/thead/tr[1]/th/text()")
    # WARNING: don't use root.xpath("/table/tbody/tr//td/text()") to extract
    # values. The XPath expression will omit empty text, causing erroneous
    # result
    tds = root.xpath("/table/tbody/tr[1]/td")
    values: List[str] = [td.text for td in tds]
    values = list(replace(values, lambda x: x == None, [""]))

    if len(keys) != len(values):
        raise RuntimeError("解析基金信息时键值对不匹配")

    responded_data = dict(zip(keys, values))

    fund_info = {}
    fund_info["净值日期"] = responded_data["净值日期"]
    fund_info["单位净值"] = responded_data["单位净值"]
    fund_info["日增长率"] = responded_data["日增长率"]
    fund_info["分红送配"] = responded_data["分红送配"]

    last_time_tds = root.xpath("/table/tbody/tr[2]/td")
    last_time_values = [td.text for td in last_time_tds]
    last_time_values = list(replace(last_time_values, lambda x: x == None, [""]))

    if len(keys) != len(values):
        raise RuntimeError("解析基金信息时键值对不匹配")

    last_time_info = dict(zip(keys, last_time_values))

    fund_info["上一天净值"] = last_time_info["单位净值"]
    fund_info["上一天净值日期"] = last_time_info["净值日期"]

    return fund_info


def fetch_estimate(fund_code: str) -> Dict[str, str]:
    # Add random parameter to the URL to break potential cache mechanism of
    # the server or the network or the requests library.
    garbage = "".join(random.sample(string.ascii_lowercase, 10))
    params = {"garbage": garbage}
    estimate_api = "http://fundgz.1234567.com.cn/js/{fund_code}.js"
    response = requests.get(estimate_api.format(fund_code=fund_code), params=params)
    response.encoding = "utf-8"
    text = response.text
    content = re.match(r"jsonpgz\((?P<content>.*)\);", text).group("content")
    json_data = json.loads(content)
    fund_info = {}
    fund_info["基金名称"] = json_data["name"]
    fund_info["估算日期"] = json_data["gztime"]
    fund_info["实时估值"] = json_data["gsz"]
    estimate_growth_rate = json_data["gszzl"]
    if "%" in estimate_growth_rate:
        fund_info["估算增长率"] = estimate_growth_rate
    else:
        fund_info["估算增长率"] = estimate_growth_rate + "%"

    return fund_info


def fetch_fund_info(fund_code: str) -> Dict[str, str]:
    try:
        fund_info = {}
        fund_info["基金代码"] = fund_code
        fund_info.update(fetch_net_value(fund_code))
        fund_info.update(fetch_estimate(fund_code))
        return fund_info
    except Exception as exc:
        raise RuntimeError(f"获取基金代码为 {fund_code} 的基金相关信息时发生错误") from exc


if __name__ == "__main__":
    print(fetch_net_value("000478"))
