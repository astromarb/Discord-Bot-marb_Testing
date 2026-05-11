from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from bot.services.json_store import JsonStore

DEFAULT_EVENTS: dict[str, Any] = {"version": "1.0", "last_sync": None, "events": []}


@dataclass(slots=True)
class CommunityEvent:
    id: str
    title: str
    description: str
    starts_at: datetime
    channel_target: str | None
    reminder_before: list[int]
    active: bool = True


class EventService:
    def __init__(self, data_path: Path) -> None:
        self.store = JsonStore(data_path, DEFAULT_EVENTS)

    async def add_event(self, title: str, description: str, starts_at: datetime, channel_target: str | None, reminders: list[int]) -> str:
        data = await self.store.read()
        event_id = f"evt_{uuid4().hex[:8]}"
        data.setdefault("events", []).append({
            "id": event_id,
            "title": title,
            "description": description,
            "starts_at": starts_at.astimezone(timezone.utc).isoformat(),
            "channel_target": channel_target,
            "reminder_before": reminders,
            "sent_reminders": [],
            "active": True,
        })
        data["last_sync"] = datetime.now(timezone.utc).isoformat()
        await self.store.write(data)
        return event_id

    async def delete_event(self, event_id: str) -> bool:
        data = await self.store.read()
        before = len(data.get("events", []))
        data["events"] = [event for event in data.get("events", []) if event.get("id") != event_id]
        removed = len(data["events"]) != before
        if removed:
            data["last_sync"] = datetime.now(timezone.utc).isoformat()
            await self.store.write(data)
        return removed

    async def upcoming_events(self, limit: int = 10) -> list[CommunityEvent]:
        data = await self.store.read()
        now = datetime.now(timezone.utc)
        events = []
        for raw in data.get("events", []):
            starts_at = datetime.fromisoformat(raw["starts_at"])
            if raw.get("active", True) and starts_at >= now:
                events.append(self._to_event(raw))
        return sorted(events, key=lambda event: event.starts_at)[:limit]

    async def mark_reminder_sent(self, event_id: str, hours_before: int) -> None:
        data = await self.store.read()
        for event in data.get("events", []):
            if event.get("id") == event_id:
                event.setdefault("sent_reminders", []).append(hours_before)
        await self.store.write(data)

    async def due_reminders(self) -> list[tuple[CommunityEvent, int]]:
        data = await self.store.read()
        now = datetime.now(timezone.utc)
        due: list[tuple[CommunityEvent, int]] = []
        for raw in data.get("events", []):
            if not raw.get("active", True):
                continue
            starts_at = datetime.fromisoformat(raw["starts_at"])
            hours_until = (starts_at - now).total_seconds() / 3600
            sent = set(raw.get("sent_reminders", []))
            for hours in raw.get("reminder_before", [24, 2]):
                if hours not in sent and 0 <= hours_until <= hours:
                    due.append((self._to_event(raw), hours))
        return due

    @staticmethod
    def _to_event(raw: dict[str, Any]) -> CommunityEvent:
        return CommunityEvent(
            id=raw["id"],
            title=raw["title"],
            description=raw.get("description", ""),
            starts_at=datetime.fromisoformat(raw["starts_at"]),
            channel_target=raw.get("channel_target"),
            reminder_before=list(raw.get("reminder_before", [24, 2])),
            active=raw.get("active", True),
        )
