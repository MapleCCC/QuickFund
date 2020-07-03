import json
import re
from typing import Any, Dict, List

import requests
from lxml import etree  # type: ignore
from more_itertools import replace

__all__ = ["get_fund_info"]

# Unfortunately current state of lxml type stub is far from complete.
# https://github.com/python/typeshed/issues/525
ETree = Any


def get_net_value(fund_code: str) -> Dict[str, str]:
    params = {"type": "lsjz", "page": 1, "per": 2, "code": fund_code}
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

    fund_info = dict(zip(keys, values))

    last_time_tds = root.xpath("/table/tbody/tr[2]/td")
    last_time_values = [td.text for td in last_time_tds]
    last_time_values = list(replace(last_time_values, lambda x: x == None, [""]))

    if len(keys) != len(values):
        raise RuntimeError("解析基金信息时键值对不匹配")

    last_time_info = dict(zip(keys, last_time_values))

    fund_info["上一天净值"] = last_time_info["单位净值"]
    fund_info["上一天净值日期"] = last_time_info["净值日期"]

    return fund_info


def get_estimate(fund_code: str) -> Dict[str, str]:
    estimate_api = "http://fundgz.1234567.com.cn/js/{fund_code}.js"
    response = requests.get(estimate_api.format(fund_code=fund_code))
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


def get_fund_info(fund_code: str) -> Dict[str, str]:
    try:
        fund_info = {}
        fund_info["基金代码"] = fund_code
        fund_info.update(get_net_value(fund_code))
        fund_info.update(get_estimate(fund_code))
        return fund_info
    except Exception as exc:
        raise RuntimeError(f"获取基金代码为 {fund_code} 的基金相关信息时发生错误") from exc


if __name__ == "__main__":
    print(get_net_value("000478"))
