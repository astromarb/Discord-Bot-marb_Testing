from __future__ import annotations

from datetime import datetime

import pytz
from dateutil.parser import isoparse, parse


def require_non_empty(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} cannot be empty.")
    return value


def parse_datetime(value: str) -> datetime:
    try:
        return isoparse(value)
    except Exception as exc:  # noqa: BLE001 - keep slash command feedback simple
        raise ValueError("Use ISO format, e.g. 2026-05-10T20:00:00-05:00 or 2026-05-10T20:00:00Z.") from exc


def parse_local_datetime(value: str, timezone_name: str) -> datetime:
    try:
        tz = pytz.timezone(timezone_name)
        dt = parse(value)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        else:
            dt = dt.astimezone(tz)
        return dt
    except Exception as exc:
        raise ValueError(f"Could not parse date/time '{value}'. Try formats like: 'May 20 8:30 PM', '05-20 2026 3:00 PM', or '2026-05-20 20:00'") from exc
