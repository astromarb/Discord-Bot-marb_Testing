from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from bot.services.event_service import EventService
from bot.services.knowledge_service import KnowledgeService


@pytest.mark.asyncio
async def test_knowledge_add_and_search(tmp_path):
    service = KnowledgeService(tmp_path / "kb.json")
    entry_id = await service.add_entry("Mining", "How do I mine?", "Bring a mining tool or ship.", ["mine", "mining"])
    matches = await service.search("mining guide", min_confidence=0.2)
    assert entry_id in {match.entry_id for match in matches}


@pytest.mark.asyncio
async def test_event_add_and_list(tmp_path):
    service = EventService(tmp_path / "events.json")
    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    event_id = await service.add_event("Fleet Night", "Training run", starts_at, "events-announcements", [24, 2])
    events = await service.upcoming_events()
    assert events[0].id == event_id
