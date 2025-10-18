from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Tuple

from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")
TIME_SLOTS = ["08:00", "12:00", "18:00", "21:00"]


def get_zoneinfo(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return UTC


def now_in_timezone(tz_name: str) -> datetime:
    tz = get_zoneinfo(tz_name)
    return datetime.now(tz)


def tomorrow_date(tz_name: str) -> date:
    now = now_in_timezone(tz_name)
    return (now + timedelta(days=1)).date()


def tomorrow_range_utc(tz_name: str) -> Tuple[datetime, datetime]:
    tomorrow = tomorrow_date(tz_name)
    tz = get_zoneinfo(tz_name)
    start_local = datetime.combine(tomorrow, time(0, 0), tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def slot_to_utc_datetime(tomorrow_local: date, slot: str, tz_name: str) -> datetime:
    hour, minute = map(int, slot.split(":"))
    tz = get_zoneinfo(tz_name)
    local_dt = datetime.combine(tomorrow_local, time(hour=hour, minute=minute), tzinfo=tz)
    return local_dt.astimezone(UTC)


def format_event_time_local(dt_utc: datetime, tz_name: str) -> str:
    tz = get_zoneinfo(tz_name)
    local_dt = dt_utc.astimezone(tz)
    return local_dt.strftime("%H:%M")
