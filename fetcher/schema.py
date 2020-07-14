from datetime import date, datetime
from typing import Any

import attr

__all__ = ["FundInfo"]

# Use language construct to make sure fieldnames consistent with
# their occurrences in other places across the code repository. As
# manually syncing them is both tedious and error-prone.

# FIXME if we set 基金代码 to string type, Excel document raises warning about
# treating number as text.

# TODO compare implementation choice between dict, user-defined class, dataclass, namedtuple, and
# attrs library.

# TODO thoroughly read through doc of dataclasses module.

# TODO thoroughly read through doc of attrs library.

# TODO read attrs library doc's section about "Why not...?"

# TODO see what features attrs has that dataclass doesn't have.
# ANSWER: slots, ..., etc.

# TODO after refactor, use binary diff to check regression.
# Turn out that we can't. Because Xlsxwriter create Excel document has different hash
# digest each time, even if we are writing identical content. A possible reason might be
# Xlsxwriter create Excel document also contain some time-related information.

# QUESTION: do we need to specify default value for fields? Have a trial and
# see what happens if we construct a dataclass without parameters while the
# dataclass contains fields that have no default values.
# ANSWER: Turn out that we can't. Try attrs library or try to use a sentinel to
# signal MISSING VALUE.

# QUESTION: can we dynamically create new property to a dataclass instance?
# ANSWER: Yes.
# WORKAROUND: Add __slots__ property, or use attrs library.
# Turn out that it's been a infamous problem that there is no simple good way to
# incorporate dataclass and slots. So we are left with using attrs library.
# Or we can use @add_slots decorator by ericvsmith.

# QUESTION: can we assign value to a field that doesn't match the type
# annotation?
# ANSWER: Yes. Type annotation doesn't impose runtime restriction, except a
# few minor situations. We should rely on static type checker to maintain the type
# restriction in code editing time.

# QUESTION: what happen if workbook.add_format({})? Will we get a default cell format, like
# what we get when calling workbook.add_format()? What about
# workbook.add_format(None)?
# ANSWER: Judging from source code of the XlsxWriter library, add_format({}) and
# add_format(None) is equivalent to default format.

# QUESTION: Does dataclass support __getitem__?
# ANSWER: No.


@attr.s(slots=True)
class FundInfo:
    基金名称: str = attr.ib(default=None, metadata={"width": 22})
    基金代码: str = attr.ib(default=None)
    上一天净值日期: date = attr.ib(
        default=None, metadata={"width": 14, "format": {"num_format": "yyyy-mm-dd"}}
    )
    上一天净值: float = attr.ib(
        default=None, metadata={"width": 10, "format": {"bg_color": "yellow"}}
    )
    净值日期: date = attr.ib(
        default=None, metadata={"width": 13, "format": {"num_format": "yyyy-mm-dd"}}
    )
    单位净值: float = attr.ib(default=None, metadata={"format": {"bg_color": "yellow"}})
    日增长率: float = attr.ib(default=None, metadata={"format": {"num_format": "0.00%"}})
    估算日期: datetime = attr.ib(
        default=None,
        metadata={"width": 17, "format": {"num_format": "yyyy-mm-dd hh:mm"}},
    )
    实时估值: float = attr.ib(
        default=None, metadata={"width": 11, "format": {"bg_color": "B4D6E4"}}
    )
    估算增长率: float = attr.ib(
        default=None, metadata={"width": 11, "format": {"num_format": "0.00%"}}
    )
    分红送配: str = attr.ib(default=None)

    def __getitem__(self, index: int) -> Any:
        return attr.astuple(self)[index]
