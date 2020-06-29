import re
import csv
from typing import Dict
from pathlib import Path

import requests
from bs4 import BeautifulSoup as bs

# TODO: remove BeautifulSoup dependency. Use solely lxml for parsing.


API = "http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&page=1&per=1&code="

content_pattern = r"var apidata={ content:\"(.*)\""


def get_info(code: str) -> Dict[str, str]:
    response = requests.get(API + code)
    response.encoding = "utf-8"
    text = response.text
    matchobj = re.match(content_pattern, text)
    if not matchobj:
        raise RuntimeError("Regex match fails")
    content = matchobj.group(1)

    soup = bs(content, "lxml")
    keys, values = soup.find_all("tr")
    keys = [th.string for th in keys.find_all("th")]
    values = [td.string for td in values.find_all("td")]

    assert len(keys) == len(values)

    return dict(zip(keys, values))


fieldnames = ["基金代码", "净值日期", "单位净值", "日增长率", "分红送配"]


def main() -> None:
    codes = Path("代码.txt").read_text(encoding="utf-8").splitlines()

    with open("总结.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames, extrasaction="ignore")

        for code in codes:
            writer.writeheader()
            info = get_info(code)
            info["基金代码"] = code
            writer.writerow(info)


if __name__ == "__main__":
    main()
