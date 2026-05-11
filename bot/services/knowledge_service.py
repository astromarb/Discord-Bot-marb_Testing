from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from uuid import uuid4

from bot.services.json_store import JsonStore

DEFAULT_KB: dict[str, Any] = {
    "version": "1.0",
    "last_updated": None,
    "categories": [
        {
            "id": "getting-started",
            "name": "Getting Started",
            "description": "Resources and guides for new pilots",
            "color": "#00FF00",
            "entries": [
                {
                    "id": "new-pilot-start",
                    "keywords": ["new", "newbie", "beginner", "start", "first day"],
                    "question": "I'm new to Star Citizen. Where should I start?",
                    "answer": "Start with the server rules, introduce yourself, and ask for a guide run. Good early loops are delivery, basic hauling, hand mining, or joining a crew as support.",
                    "priority": 1,
                }
            ],
        },
        {
            "id": "gameplay-loops",
            "name": "Gameplay Loops",
            "description": "Mining, hauling, salvage, combat, exploration, and logistics",
            "color": "#42A5F5",
            "entries": [],
        },
    ],
    "unanswered": [],
}


@dataclass(slots=True)
class KnowledgeMatch:
    category: str
    entry_id: str
    question: str
    answer: str
    confidence: float


class KnowledgeService:
    def __init__(self, data_path: Path) -> None:
        self.store = JsonStore(data_path, DEFAULT_KB)

    async def search(self, query: str, *, min_confidence: float = 0.0) -> list[KnowledgeMatch]:
        data = await self.store.read()
        query_norm = query.lower().strip()
        matches: list[KnowledgeMatch] = []

        for category in data.get("categories", []):
            for entry in category.get("entries", []):
                haystacks = [entry.get("question", ""), *entry.get("keywords", [])]
                keyword_hits = sum(1 for keyword in entry.get("keywords", []) if keyword.lower() in query_norm)
                similarity = max((SequenceMatcher(None, query_norm, str(text).lower()).ratio() for text in haystacks), default=0)
                confidence = min(1.0, similarity + (keyword_hits * 0.2) + (0.05 / max(entry.get("priority", 1), 1)))
                if confidence >= min_confidence:
                    matches.append(KnowledgeMatch(
                        category=category.get("name", "Uncategorized"),
                        entry_id=entry.get("id", "unknown"),
                        question=entry.get("question", ""),
                        answer=entry.get("answer", ""),
                        confidence=confidence,
                    ))

        return sorted(matches, key=lambda item: item.confidence, reverse=True)

    async def add_entry(self, category_name: str, question: str, answer: str, keywords: list[str]) -> str:
        data = await self.store.read()
        category = self._find_or_create_category(data, category_name)
        entry_id = f"kb_{uuid4().hex[:8]}"
        category.setdefault("entries", []).append({
            "id": entry_id,
            "keywords": [keyword.strip().lower() for keyword in keywords if keyword.strip()],
            "question": question.strip(),
            "answer": answer.strip(),
            "priority": 1,
        })
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        await self.store.write(data)
        return entry_id

    async def delete_entry(self, entry_id: str) -> bool:
        data = await self.store.read()
        removed = False
        for category in data.get("categories", []):
            before = len(category.get("entries", []))
            category["entries"] = [entry for entry in category.get("entries", []) if entry.get("id") != entry_id]
            removed = removed or len(category["entries"]) != before
        if removed:
            data["last_updated"] = datetime.now(timezone.utc).isoformat()
            await self.store.write(data)
        return removed

    async def list_entries(self, category_filter: str | None = None) -> list[dict[str, str]]:
        data = await self.store.read()
        rows: list[dict[str, str]] = []
        for category in data.get("categories", []):
            if category_filter and category_filter.lower() not in category.get("name", "").lower():
                continue
            for entry in category.get("entries", []):
                rows.append({"id": entry.get("id", ""), "category": category.get("name", ""), "question": entry.get("question", "")})
        return rows

    async def record_unanswered(self, question: str, author_id: int, channel_id: int) -> None:
        data = await self.store.read()
        data.setdefault("unanswered", []).append({
            "question": question,
            "author_id": author_id,
            "channel_id": channel_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        await self.store.write(data)

    @staticmethod
    def _find_or_create_category(data: dict[str, Any], name: str) -> dict[str, Any]:
        for category in data.setdefault("categories", []):
            if category.get("name", "").lower() == name.lower():
                return category
        category = {"id": name.lower().replace(" ", "-"), "name": name, "description": "", "color": "#00FF00", "entries": []}
        data["categories"].append(category)
        return category
