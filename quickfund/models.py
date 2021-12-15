from __future__ import annotations

from datetime import date, datetime, time, timedelta

import attr

from .utils.datetime import china_now, is_weekend, last_friday


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

    def is_latest(self) -> bool:
        """
        Check if the fund net value info is the latest.

        Take advantage of the knowledge that fund net value info stays the same
        within 0:00 to 20:00.

        Net value date should be of China timezone.

        False negative is allowed while false positivie is not allowed.
        """

        now = china_now()
        now_time = now.time()
        today = china_now.date()
        yesterday = today - timedelta(days=1)

        if is_weekend(today):
            return self.净值日期 == last_friday(today)

        if time.min <= now_time < time(20):
            return self.净值日期 == yesterday
        else:
            return self.净值日期 == today


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
        )  # type: ignore # FIXME https://github.com/python-attrs/attrs/issues/795


def is_market_opening(_time: time = None) -> bool:
    _time = _time or datetime.now().time()
    return time(9, 30) <= _time <= time(11, 30) or time(13) <= _time <= time(15)


def last_market_close_datetime(_datetime: datetime = None) -> datetime:

    _datetime = _datetime or datetime.now()
    _date, _time = _datetime.date(), _datetime.time()

    if is_weekend(_date):
        return datetime.combine(last_friday(_date), time(15))

    if time.min <= _time < time(11, 30):
        yesterday = _date - timedelta(days=1)
        return datetime.combine(yesterday, time(15))

    elif time(11, 30) <= _time < time(15):
        return datetime.combine(_date, time(11, 30))

    else:
        return datetime.combine(_date, time(15))


def estimate_datetime_is_latest(estimate_datetime: datetime) -> bool:
    """
    Check if the estimate datetime is the latest.

    Take advantage of the knowledge that estimate info stays the same
    within 15:00 to next day 9:30.

    `estimate_datetime` should be of China timezone.

    False negative is allowed while false positivie is not allowed.
    """

    now = china_now()

    if is_market_opening(now.time()):
        return False
    else:
        return estimate_datetime == last_market_close_datetime(now)


def IARBC_date_is_latest(IARBC_date: date) -> bool:
    """
    Check if the IARBC date is the latest.

    `IARBC_date` should be of China timezone.
    """

    # TODO what's the update pattern of IARBC info? Currently only a naive approach,
    # not efficient enough.

    today = china_now().date()
    return IARBC_date == today
