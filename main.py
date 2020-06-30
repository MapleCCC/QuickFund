import csv
import io
import os
import re
from pathlib import Path
from typing import Dict

import click
import requests
from lxml import etree  # type: ignore
from pandas import pandas as pd

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
            raise RuntimeError("解析基金信息时键值对不匹配")

        return dict(zip(keys, values))
    except Exception as exc:
        raise RuntimeError(f"获取基金代码为{code}的基金相关信息时发生错误") from exc


fieldnames = ["基金代码", "净值日期", "单位净值", "日增长率", "分红送配"]


@click.command()
@click.argument("filename")
@click.option("-o", "--output", default="基金信息.xlsx")
def main(filename: str, output: str) -> None:
    in_filename = filename
    out_filename = output

    if not os.path.exists(in_filename):
        raise FileNotFoundError(f"文件 {in_filename} 不存在")

    if os.path.isdir(out_filename):
        raise RuntimeError(f"同名文件夹已存在，无法新建文件 {out_filename}")

    if os.path.isfile(out_filename):
        while True:
            choice = input(
                f"{out_filename} 同名文件已存在，是否覆盖之？【选择是请输入“是”，选择否请输入“否”】\n"
            ).strip()
            if choice == "是":
                break
            elif choice == "否":
                exit()
            else:
                print("输入指令无效，请重新输入")

    codes = Path(in_filename).read_text(encoding="utf-8").splitlines()

    ss = io.StringIO(newline="")

    writer = csv.DictWriter(ss, fieldnames, extrasaction="ignore")
    writer.writeheader()
    for i, code in enumerate(codes):
        _code = code.strip()
        if re.fullmatch(code_pattern, _code):
            info = get_info(_code)
            info["基金代码"] = _code
            writer.writerow(info)
        else:
            print(f"第{i}行内容不是有效的基金代码: {code}，暂且跳过之")

    ss.seek(0)

    pd.read_csv(ss).to_excel(out_filename, index=None, header=True)  # type: ignore


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
