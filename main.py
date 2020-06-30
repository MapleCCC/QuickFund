import csv
import os
import re
from pathlib import Path
from typing import Dict

import click
import requests
from lxml import etree  # type: ignore

API = "http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&page=1&per=1&code="

content_pattern = r"var apidata={ content:\"(.*)\""
code_pattern = r"\d{6}"


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

        if len(keys) != len(values):
            raise RuntimeError()

        return dict(zip(keys, values))
    except:
        raise RuntimeError(f"获取基金代码为{code}的基金相关信息时发生错误")


fieldnames = ["基金代码", "净值日期", "单位净值", "日增长率", "分红送配"]


@click.command()
@click.argument("filename")
@click.option("-o", "--output", default="基金信息.csv")
def main(filename: str, output: str) -> None:
    in_filename = filename
    out_filename = output

    if not os.path.exists(in_filename):
        raise FileNotFoundError(f"文件{in_filename}不存在")

    codes = Path(in_filename).read_text(encoding="utf-8").splitlines()

    with open(out_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames, extrasaction="ignore")

        writer.writeheader()
        for i, code in enumerate(codes):
            _code = code.strip()
            if re.fullmatch(code_pattern, _code):
                info = get_info(_code)
                info["基金代码"] = _code
                writer.writerow(info)
            else:
                print(f"第{i}行内容不是有效的基金代码: {code}，暂且跳过之")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
