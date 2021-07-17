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


@attr.s
class FundInfo(FundNetValueInfo, FundEstimateInfo):
    """
    A dataclass to represent fund info.
    """

    def replace(
        self,
        net_value_info: FundNetValueInfo = None,
        estimate_info: FundEstimateInfo = None,
    ) -> None:

        if net_value_info is not None:
            for attribute, value in attr.asdict(net_value_info).items():
                setattr(self, attribute, value)

        if estimate_info is not None:
            for attribute, value in attr.asdict(estimate_info).items():
                setattr(self, attribute, value)

    @classmethod
    def combine(
        cls, net_value_info: FundNetValueInfo, estimate_info: FundEstimateInfo
    ) -> FundInfo:
        return cls(
            **attr.asdict(net_value_info), **attr.asdict(estimate_info)
        )  # type: ignore # https://github.com/python-attrs/attrs/issues/795
