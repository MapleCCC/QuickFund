import csv
import re
from pathlib import Path
from typing import Dict

import click
import requests
from lxml import etree  # type: ignore

API = "http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&page=1&per=1&code="

content_pattern = r"var apidata={ content:\"(.*)\""


def get_info(code: str) -> Dict[str, str]:
    try:
        response = requests.get(API + code)
        response.encoding = "utf-8"
        text = response.text
        content = re.match(content_pattern, text).group(1)

        root = etree.XML(content)
        keys = root.xpath("/table/thead/tr//th/text()")
        tds = root.xpath("/table/tbody/tr//td")
        values = [td.text for td in tds]

        assert len(keys) == len(values)

        return dict(zip(keys, values))
    except:
        raise RuntimeError(f"Error when attempting to get info of 基金代码: {code}")


fieldnames = ["基金代码", "净值日期", "单位净值", "日增长率", "分红送配"]


@click.command()
@click.argument("filename")
def main(filename: str) -> None:
    codes = Path(filename).read_text(encoding="utf-8").splitlines()

    with open("总结.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames, extrasaction="ignore")

        writer.writeheader()
        for code in codes:
            assert len(code) == 6
            info = get_info(code)
            info["基金代码"] = code
            writer.writerow(info)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
