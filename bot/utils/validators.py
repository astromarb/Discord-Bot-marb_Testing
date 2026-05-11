from __future__ import annotations

from datetime import datetime

from dateutil.parser import isoparse


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
