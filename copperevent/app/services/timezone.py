from __future__ import annotations

import re
from typing import Optional

from ..config import settings
from ..repositories import UserRepository
from ..utils.dates import get_zoneinfo

TZ_PATTERN = re.compile(r"^[A-Za-z0-9_./+-]+$")


def get_default_timezone() -> str:
    return settings.default_tz


def is_valid_timezone(tz_name: str) -> bool:
    if not tz_name or not TZ_PATTERN.match(tz_name):
        return False
    try:
        get_zoneinfo(tz_name)
    except Exception:
        return False
    return True


def update_user_timezone(user_repo: UserRepository, user, tz_name: str) -> bool:
    if not is_valid_timezone(tz_name):
        return False
    user_repo.update_timezone(user, tz_name)
    return True
