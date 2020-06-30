import json
import re
from functools import lru_cache
from typing import Dict, List, Tuple

import requests
from lxml import etree  # type: ignore
from more_itertools import replace

__all__ = ["get_fund_info"]

net_value_api = (
    "https://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&page=1&per=1&code="
)
search_api = (
    "https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?m=1&key="
)
fund_page_url = "http://fund.eastmoney.com/{code}.html"


@lru_cache(maxsize=None)
def get_fund_name(code: str) -> str:
    try:
        response = requests.get(search_api + code)
        response.encoding = "utf-8"
        json_data = json.loads(response.text)
        candidates = json_data["Datas"]
        if len(candidates) == 0:
            raise RuntimeError(f"没有找到代码为 {code} 的基金")
        elif len(candidates) > 1:
            raise RuntimeError(f"找到了不止一个基金的代码是 {code}")

        return candidates[0]["NAME"]
    except Exception as exc:
        raise RuntimeError(f"获取基金代码为 {code} 的基金名称信息时发生错误") from exc


@lru_cache(maxsize=None)
def get_fund_net_value_estimate(code: str) -> Tuple[str, str, str]:
    try:
        response = requests.get(fund_page_url.format(code=code))
        response.encoding = "utf-8-sig"
        html = etree.HTML(response.text)
        estimate_timestamp = html.xpath('//span[@id="gz_gztime"]/text()')[0]
        estimate = html.xpath('//span[@id="gz_gsz"]/text()')[0]
        estimate_growth_rate = html.xpath('//span[@id="gz_gszzl"]/text()')[0]
        return estimate_timestamp, estimate, estimate_growth_rate
    except Exception as exc:
        raise RuntimeError(f"获取基金代码为 {code} 的基金的估算值相关信息时发生错误") from exc


@lru_cache(maxsize=None)
def get_fund_info(code: str) -> Dict[str, str]:
    try:
        response = requests.get(net_value_api + code)
        response.encoding = "utf-8"
        text = response.text
        content = re.match(r"var apidata={ content:\"(?P<content>.*)\"", text).group(
            "content"
        )

        root = etree.XML(content)
        keys = root.xpath("/table/thead/tr//th/text()")
        # WARNING: don't use root.xpath("/table/tbody/tr//td/text()") to extract
        # values. The XPath expression will omit empty text, causing erroneous
        # result
        tds = root.xpath("/table/tbody/tr//td")
        values: List[str] = [td.text for td in tds]
        values = list(replace(values, lambda x: x == None, [""]))

        if len(keys) != len(values):
            raise RuntimeError("解析基金信息时键值对不匹配")

        info = dict(zip(keys, values))
        info["基金代码"] = code
        info["基金名称"] = get_fund_name(code)
        info["估算日期"], info["实时估算值"], info["估算增长率"] = get_fund_net_value_estimate(code)

        return info

    except Exception as exc:
        raise RuntimeError(f"获取基金代码为 {code} 的基金相关信息时发生错误") from exc
