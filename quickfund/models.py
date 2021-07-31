from __future__ import annotations

from datetime import date, datetime

import attr


__all__ = ["FundNetValueInfo", "FundEstimateInfo", "FundInfo"]


@attr.s(auto_attribs=True)
class FundNetValueInfo:
    """
    A dataclass to represent fund net value info.
    """

    净值日期: date
    单位净值: float
    日增长率: float
    分红送配: str
    上一天净值: float
    上一天净值日期: date


@attr.s(auto_attribs=True)
class FundEstimateInfo:
    """
    A dataclass to represent fund estimate info.
    """

    基金代码: str
    基金名称: str
    估算日期: datetime
    实时估值: float
    估算增长率: float


@attr.s(auto_attribs=True)
class FundIARBCInfo:
    """
    A dataclass to represent fund IARBC (Increase Amount Ranking by Category) info.
    """

    同类排名截止日期: date
    近1周同类排名: str
    近1月同类排名: str
    近3月同类排名: str
    近6月同类排名: str
    今年来同类排名: str
    近1年同类排名: str
    近2年同类排名: str
    近3年同类排名: str


@attr.s
class FundInfo(FundNetValueInfo, FundEstimateInfo, FundIARBCInfo):
    """
    A dataclass to represent fund info.
    """

    def replace(
        self,
        net_value_info: FundNetValueInfo = None,
        estimate_info: FundEstimateInfo = None,
        IARBC_info: FundIARBCInfo = None,
    ) -> None:

        if net_value_info is not None:
            for attribute, value in attr.asdict(net_value_info).items():
                setattr(self, attribute, value)

        if estimate_info is not None:
            for attribute, value in attr.asdict(estimate_info).items():
                setattr(self, attribute, value)

        if IARBC_info is not None:
            for attribute, value in attr.asdict(IARBC_info).items():
                setattr(self, attribute, value)

    @classmethod
    def combine(
        cls,
        net_value_info: FundNetValueInfo,
        estimate_info: FundEstimateInfo,
        IARBC_info: FundIARBCInfo,
    ) -> FundInfo:
        return cls(
            **attr.asdict(net_value_info),
            **attr.asdict(estimate_info),
            **attr.asdict(IARBC_info)
        )  # type: ignore # https://github.com/python-attrs/attrs/issues/795
