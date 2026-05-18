from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from aiohttp import web

from bot.utils.formatters import make_embed
from bot.utils.validators import parse_local_datetime

if TYPE_CHECKING:
    from bot.client import StarCitizenHubBot

log = logging.getLogger("starcitizen_hub.dashboard")

DASHBOARD_DIR = Path(__file__).resolve().parents[2] / "dashboard"

ANNOUNCEMENT_COLORS = {
    "paste_purple": 0xB39DDB,
    "cyan": 0x00BCD4,
    "orange": 0xFF9800,
    "teal": 0x009688,
}


class AuditLog:
    def __init__(self, max_entries: int = 200) -> None:
        self._entries: deque[dict] = deque(maxlen=max_entries)

    def add(self, action: str, details: str, user: str = "system") -> None:
        self._entries.appendleft({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "details": details,
            "user": user,
        })

    def list(self, limit: int = 50) -> list[dict]:
        return list(self._entries)[:limit]


class DashboardService:
    def __init__(self, bot: "StarCitizenHubBot", host: str = "0.0.0.0", port: int = 8080) -> None:
        self.bot = bot
        self.host = host
        self.port = port
        self.audit = AuditLog()
        self.app = web.Application()
        self.runner: web.AppRunner | None = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.app.router.add_get("/", self.index)
        self.app.router.add_get("/api/overview", self.api_overview)
        self.app.router.add_get("/api/knowledge", self.api_knowledge)
        self.app.router.add_post("/api/knowledge", self.api_knowledge_add)
        self.app.router.add_delete("/api/knowledge/{entry_id}", self.api_knowledge_delete)
        self.app.router.add_get("/api/events", self.api_events)
        self.app.router.add_post("/api/events", self.api_events_add)
        self.app.router.add_delete("/api/events/{event_id}", self.api_events_delete)
        self.app.router.add_get("/api/audit", self.api_audit)
        self.app.router.add_get("/api/config", self.api_config)
        self.app.router.add_get("/api/channels", self.api_channels)
        self.app.router.add_post("/api/announce", self.api_announce)

    async def index(self, request: web.Request) -> web.Response:
        index_path = DASHBOARD_DIR / "index.html"
        if not index_path.exists():
            return web.Response(text="Dashboard not found.", status=404)
        return web.FileResponse(index_path)

    async def api_overview(self, request: web.Request) -> web.Response:
        entries = await self.bot.knowledge.list_entries()
        events = await self.bot.events.upcoming_events()
        guild_info = []
        for guild in self.bot.guilds:
            guild_info.append({
                "id": str(guild.id),
                "name": guild.name,
                "member_count": guild.member_count,
                "channel_count": len(guild.channels),
            })
        return web.json_response({
            "guilds": len(self.bot.guilds),
            "knowledge_entries": len(entries),
            "upcoming_events": len(events),
            "latency_ms": round(self.bot.latency * 1000) if self.bot.latency else None,
            "user": str(self.bot.user) if self.bot.user else None,
            "guild_list": guild_info,
        })

    async def api_knowledge(self, request: web.Request) -> web.Response:
        category = request.query.get("category")
        entries = await self.bot.knowledge.list_entries(category)
        return web.json_response({"entries": entries})

    async def api_knowledge_add(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            category = data.get("category", "").strip()
            question = data.get("question", "").strip()
            answer = data.get("answer", "").strip()
            keywords = [k.strip() for k in data.get("keywords", "").split(",") if k.strip()]
            if not all([category, question, answer]):
                return web.json_response({"error": "category, question, and answer are required"}, status=400)
            entry_id = await self.bot.knowledge.add_entry(category, question, answer, keywords)
            self.audit.add("knowledge.add", f"Added entry '{question[:60]}' to {category}", "dashboard")
            return web.json_response({"id": entry_id, "ok": True})
        except Exception as exc:
            return web.json_response({"error": str(exc)}, status=400)

    async def api_knowledge_delete(self, request: web.Request) -> web.Response:
        entry_id = request.match_info["entry_id"]
        removed = await self.bot.knowledge.delete_entry(entry_id)
        if removed:
            self.audit.add("knowledge.delete", f"Deleted entry {entry_id}", "dashboard")
        return web.json_response({"ok": removed})

    async def api_events(self, request: web.Request) -> web.Response:
        events = await self.bot.events.upcoming_events(limit=50)
        return web.json_response({
            "events": [
                {
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "starts_at": event.starts_at.isoformat(),
                    "channel_target": event.channel_target,
                    "reminder_before": event.reminder_before,
                }
                for event in events
            ]
        })

    async def api_events_add(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            title = data.get("title", "").strip()
            description = data.get("description", "").strip()
            date_time = data.get("date_time", "").strip()
            channel = data.get("channel") or None
            reminders_raw = data.get("reminders", "24,2")
            if not all([title, description, date_time]):
                return web.json_response({"error": "title, description, and date_time are required"}, status=400)
            tz = self.bot.config_data.get("timezone", "America/Chicago")
            parsed_dt = parse_local_datetime(date_time, tz)
            reminders = [int(r.strip()) for r in str(reminders_raw).split(",") if str(r).strip()]
            event_id = await self.bot.events.add_event(title, description, parsed_dt, channel, reminders)
            self.audit.add("events.add", f"Created event '{title}'", "dashboard")
            return web.json_response({"id": event_id, "ok": True})
        except Exception as exc:
            return web.json_response({"error": str(exc)}, status=400)

    async def api_events_delete(self, request: web.Request) -> web.Response:
        event_id = request.match_info["event_id"]
        removed = await self.bot.events.delete_event(event_id)
        if removed:
            self.audit.add("events.delete", f"Deleted event {event_id}", "dashboard")
        return web.json_response({"ok": removed})

    async def api_audit(self, request: web.Request) -> web.Response:
        return web.json_response({"entries": self.audit.list(limit=100)})

    async def api_config(self, request: web.Request) -> web.Response:
        return web.json_response({
            "bot_name": self.bot.config_data.get("bot.name", "Nexus AI Hub"),
            "moderator_roles": self.bot.config_data.get("permissions.moderator_roles", []),
            "channels": {
                "welcome": self.bot.config_data.get("server.welcome_channel"),
                "rules": self.bot.config_data.get("server.rules_channel"),
                "general": self.bot.config_data.get("server.general_channel"),
                "admin": self.bot.config_data.get("server.admin_channel"),
                "events": self.bot.config_data.get("server.events_channel"),
            },
            "onboarding": {
                "enabled": self.bot.config_data.get("onboarding.enabled", True),
                "followup_dm_hours": self.bot.config_data.get("onboarding.followup_dm_hours", 24),
            },
            "knowledge_base": {
                "min_confidence_threshold": self.bot.config_data.get("knowledge_base.min_confidence_threshold", 0.55),
            },
            "moderation": {
                "log_joins": self.bot.config_data.get("moderation.log_joins", True),
                "log_leaves": self.bot.config_data.get("moderation.log_leaves", True),
                "log_message_deletions": self.bot.config_data.get("moderation.log_message_deletions", True),
            },
        })

    async def api_channels(self, request: web.Request) -> web.Response:
        channels = []
        for guild in self.bot.guilds:
            for ch in guild.text_channels:
                channels.append({"id": str(ch.id), "name": ch.name, "guild": guild.name})
        return web.json_response({"channels": channels})

    async def api_announce(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            channel_id = data.get("channel_id")
            title = data.get("title", "").strip()
            message = data.get("message", "").strip()
            color_key = data.get("color", "paste_purple")
            if not all([channel_id, title, message]):
                return web.json_response({"error": "channel_id, title, and message are required"}, status=400)
            target = None
            for guild in self.bot.guilds:
                target = guild.get_channel(int(channel_id))
                if target:
                    break
            if not isinstance(target, discord.TextChannel):
                return web.json_response({"error": "Channel not found"}, status=404)
            hex_color = ANNOUNCEMENT_COLORS.get(color_key, ANNOUNCEMENT_COLORS["paste_purple"])
            await target.send(embed=make_embed(title, message, color=hex_color))
            self.audit.add("announce", f"Sent '{title}' to #{target.name}", "dashboard")
            return web.json_response({"ok": True})
        except Exception as exc:
            return web.json_response({"error": str(exc)}, status=400)

    async def start(self) -> None:
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        log.info("Dashboard available at http://%s:%s", self.host, self.port)

    async def stop(self) -> None:
        if self.runner:
            await self.runner.cleanup()
            log.info("Dashboard server stopped.")
