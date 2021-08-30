from datetime import date, datetime, timedelta, timezone


__all__ = ["is_weekend", "last_friday", "china_now"]


WEEKENDS = frozenset({5, 6})


def is_weekend(_date: date = None) -> bool:
    _date = _date or datetime.now().date()
    return _date.weekday() in WEEKENDS


def last_friday(_date: date = None) -> date:
    _date = _date or datetime.now().date()
    delta = timedelta(days=-(_date.weekday() + 3) % 7)
    return _date + delta


CHINA_TIMEZONE = timezone(timedelta(hours=8), name="UTC+8")


def china_now() -> datetime:
    return datetime.now(CHINA_TIMEZONE)
