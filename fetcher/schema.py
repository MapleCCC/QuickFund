from dataclasses import dataclass
from enum import Enum, auto, unique

__all__ = ["FieldType", "Field", "excel_table_schema"]

# Use language construct to make sure fieldnames consistent with
# their occurrences in other places across the code repository. As
# manually syncing them is both tedious and error-prone.

# FIXME if we set 基金代码 to string type, Excel document raises warning about
# treating number as text.


@unique
class FieldType(Enum):
    string = auto()
    date = auto()
    number = auto()


@unique
class FieldName(Enum):
    基金名称 = auto()
    基金代码 = auto()
    上一天净值日期 = auto()
    上一天净值 = auto()
    净值日期 = auto()
    单位净值 = auto()
    日增长率 = auto()
    估算日期 = auto()
    实时估值 = auto()
    估算增长率 = auto()
    分红送配 = auto()


@dataclass
class FundInfo:
    基金名称: str
    基金代码: str
    上一天净值日期: str
    上一天净值: str
    净值日期: str
    单位净值: str
    日增长率: str
    估算日期: str
    实时估值: str
    估算增长率: str
    分红送配: str


@dataclass
class Field:
    name: str
    typ: FieldType


excel_table_schema = [
    Field("基金名称", Field.string),
    Field("基金代码", Field.string),
    Field("上一天净值日期", Field.date),
    Field("上一天净值", Field.number),
    Field("净值日期", Field.date),
    Field("单位净值", Field.number),
    Field("日增长率", Field.number),
    Field("估算日期", Field.date),
    Field("实时估值", Field.number),
    Field("估算增长率", Field.number),
    Field("分红送配", Field.string),
]
