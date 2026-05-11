from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any


class JsonStore:
    """Small async-safe JSON file store for moderator-editable bot state."""

    def __init__(self, path: Path, default: dict[str, Any]) -> None:
        self.path = path
        self.default = default
        self._lock = asyncio.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps(default, indent=2), encoding="utf-8")

    async def read(self) -> dict[str, Any]:
        async with self._lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

    async def write(self, data: dict[str, Any]) -> None:
        async with self._lock:
            temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
            temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            temp_path.replace(self.path)
