#!/usr/bin/env python3

import re
import shutil
import sys
import traceback
from pathlib import Path

import click
import colorama
import semver

from .__version__ import __version__
from .config import REPO_NAME, REPO_OWNER
from .getter import get_fund_infos
from .github_utils import get_latest_release_version
from .utils import Logger, bright_blue, pause_at_exit, print_traceback_digest
from .writter import write_to_xlsx


# TODO
# GUI feature of tqdm is experimental. And our application is too fast for the plot to render.
# from tqdm.gui import tqdm, trange


ERR_LOG_FILE = "错误日志.txt"

logger = Logger()


def backup_old_outfile(out_file: Path) -> None:
    if not out_file.is_file():
        return

    # If out_file already exists, make a backup.

    backup_filename = out_file.with_name(f"[备份] {out_file.name}")
    logger.log(f'"{out_file}" 同名文件已存在，备份至 "{backup_filename}"')

    try:
        shutil.move(out_file, backup_filename)

    except PermissionError:
        raise RuntimeError(
            "备份 Excel 文档时发生权限错误，有可能是 Excel 文档已经被其他程序占用，"
            f'有可能是 "{out_file}" 已经被 Excel 打开，'
            "请关闭文件之后重试"
        ) from None


def check_update() -> None:
    """
    Check if update to the program is available.
    """

    logger.log("获取最新分发版本号......")
    # TODO Handle the case when the latest release's tag name is not semantic
    # version.
    # TODO Handle the case when the latest release's tag name is semantic version but
    # with additional suffix, like rc (release candidate), build, etc.
    try:
        latest_version = get_latest_release_version(REPO_OWNER, REPO_NAME)
    except:
        logger.log("获取最新分发版本号的时候发生错误，暂时跳过。可以通过 --update 命令来手动触发更新检查")
        return

    if semver.compare(latest_version.lstrip("v"), __version__.lstrip("v")) > 0:
        logger.log(
            f"检测到更新版本 {latest_version}，请手动至 https://github.com/MapleCCC/QuickFund/releases 下载最新版本"
        )
        sys.exit()
    else:
        logger.log("当前已是最新版本")


def is_fund_code(s: str) -> bool:
    """Check if the string represents a valid fund code"""
    return bool(re.fullmatch(r"[0-9]{6}", s))


@click.command(
    name="QuickFund",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.argument(
    "file",
    nargs=1,
    metavar="<A file containing fund codes, one code per line>",
    # TODO how to use path_type argument to convert to pathlib.Path ?
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "-o",
    "--output",
    default="基金信息.xlsx",
    show_default=True,
    # TODO how to use path_type argument to convert to pathlib.Path ?
    type=click.Path(dir_okay=False, writable=True),
    help="The output file path.",
)
@click.option("--disable-update-check", is_flag=True, help="Disable update check.")
@click.option(
    "--color-off",
    is_flag=True,
    help="Turn off the color output. For compatibility with environment without color code support.",
)
@click.option("--disable-cache", is_flag=True)
# @click.option("-v", "--versbose", is_flag=True, help="Increase verboseness")
# TODO: @click.option("--update")
@click.version_option(version=__version__)
def main(
    file: str,
    output: str,
    disable_update_check: bool,
    color_off: bool,
    disable_cache: bool,
) -> None:
    """
    A script to fetch various fund information from https://fund.eastmoney.com,
    and structuralize into Excel document.

    Input file format: one fund code per line.
    """

    colorama.init(convert=not color_off)

    pause_at_exit(info=bright_blue("按任意键以退出 ..."))

    try:
        # TODO Remove update check logic after switching architecture to
        # server/client model
        if not disable_update_check:
            print("检查更新......")
            check_update()

        in_file = Path(file)
        out_file = Path(output)

        logger.log("获取基金代码列表......")
        lines = in_file.read_text(encoding="utf-8").splitlines()
        fund_codes = [line.strip() for line in lines if is_fund_code(line.strip())]

        if not fund_codes:
            logger.log("没有发现基金代码")
            sys.exit()

        logger.log("获取基金相关信息......")
        fund_infos = get_fund_infos(fund_codes, disable_cache=disable_cache)

        logger.log("将基金相关信息写入 Excel 文件......")
        backup_old_outfile(out_file)
        write_to_xlsx(fund_infos, out_file, logger)

        # The emoji takes inspiration from the black project (https://github.com/psf/black)
        logger.log("完满结束! ✨ 🍰 ✨")

    except Exception:

        logger.log("Oops! 程序运行过程中遇到了错误，打印错误信息摘要如下：")
        print_traceback_digest()

        with open(ERR_LOG_FILE, "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        logger.log(f'详细错误信息已写入日志文件 "{ERR_LOG_FILE}"，请将日志文件提交给开发者进行调试 debug')


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
