from pathlib import Path

import xlsxwriter

from .models import FundInfo
from .utils.tqdm import tenumerate
from .utils.misc import Logger, on_failure_raises


__all__ = ["write_to_xlsx"]


@on_failure_raises(RuntimeError, "获取基金信息并写入 Excel 文档 {xlsx_filename} 的时候发生错误")
def write_to_xlsx(
    fund_infos: list[FundInfo],
    xlsx_filename: Path,
    logger: Logger = Logger.null_logger(),
) -> None:
    """
    Structuralize a list of fund infos to an Excel document.

    Input: a list of fund infos, and an Excel filename.
    """

    # TODO profile to see whether and how much setting constant_memory improves
    # performance.
    with xlsxwriter.Workbook(xlsx_filename) as workbook:

        logger.log("新建 Excel 文档......")
        worksheet = workbook.add_worksheet()

        schema = [
            {"name": "基金名称", "width": 22},
            {"name": "基金代码"},
            {"name": "上一天净值日期", "width": 14, "format": {"num_format": "yyyy-mm-dd"}},
            {"name": "上一天净值", "width": 10, "format": {"bg_color": "yellow"}},
            {"name": "净值日期", "width": 13, "format": {"num_format": "yyyy-mm-dd"}},
            {"name": "单位净值", "format": {"bg_color": "yellow"}},
            {"name": "日增长率", "format": {"num_format": "0.00%"}},
            {"name": "估算日期", "width": 17, "format": {"num_format": "yyyy-mm-dd hh:mm"}},
            {"name": "实时估值", "width": 11, "format": {"bg_color": "B4D6E4"}},
            {"name": "估算增长率", "width": 11, "format": {"num_format": "0.00%"}},
            {"name": "分红送配"},
            {"name": "近1周同类排名", "width": 13},
            {"name": "近1月同类排名", "width": 13},
            {"name": "近3月同类排名", "width": 13},
            {"name": "近6月同类排名", "width": 13},
            {"name": "今年来同类排名", "width": 13},
            {"name": "近1年同类排名", "width": 13},
            {"name": "近2年同类排名", "width": 13},
            {"name": "近3年同类排名", "width": 13},
        ]

        logger.log("调整列宽......")
        for col, field in enumerate(schema):
            # FIXME Despite the xlsxwriter doc saying that set_column(i, i, None) doesn't
            # change the column width, some simple tests show that it does. The source
            # code of xlsxwriter is too complex that I can't figure out where the
            # bug originates.
            worksheet.set_column(col, col, field.get("width"))

        header_format = workbook.add_format(
            dict(bold=True, align="center", valign="top", border=1)
        )

        logger.log("写入文档头......")
        for col, field in enumerate(schema):
            worksheet.write_string(0, col, field["name"], header_format)

        cell_formats = [workbook.add_format(field.get("format")) for field in schema]

        logger.log("写入文档体......")
        for row, fund_info in tenumerate(fund_infos, start=1, unit="行", desc="写入基金信息"):
            for col, field in enumerate(schema):
                # Judging from source code of xlsxwriter, add_format(None) is equivalent
                # to default format.
                worksheet.write(
                    row, col, getattr(fund_info, field["name"]), cell_formats[col]
                )

        logger.log("Flush 到硬盘......")
