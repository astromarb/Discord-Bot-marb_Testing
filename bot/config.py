from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"


def deep_get(data: dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    cursor: Any = data
    for part in dotted_path.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return default
        cursor = cursor[part]
    return cursor


@dataclass(frozen=True)
class BotConfig:
    token: str
    client_id: int | None
    guild_id: int | None
    timezone: str
    log_level: str
    settings: dict[str, Any]
    messages: dict[str, Any]

    def get(self, dotted_path: str, default: Any = None) -> Any:
        return deep_get(self.settings, dotted_path, default)

    def message(self, dotted_path: str, default: Any = None) -> Any:
        return deep_get(self.messages, dotted_path, default)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _optional_int(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Expected an integer Discord id, got {raw!r}") from exc


def load_config() -> BotConfig:
    load_dotenv(ROOT_DIR / ".env")
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is missing. Copy .env.example to .env and add your bot token.")

    settings = _load_yaml(CONFIG_DIR / "settings.yaml")
    messages = _load_yaml(CONFIG_DIR / "messages.yaml")

    return BotConfig(
        token=token,
        client_id=_optional_int(os.getenv("DISCORD_CLIENT_ID")),
        guild_id=_optional_int(os.getenv("DISCORD_GUILD_ID")),
        timezone=os.getenv("TIMEZONE", settings.get("timezone", "UTC")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        settings=settings,
        messages=messages,
    )
