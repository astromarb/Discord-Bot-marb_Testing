from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from bot.client import StarCitizenHubBot

log = logging.getLogger("starcitizen_hub.dashboard")

DASHBOARD_DIR = Path(__file__).resolve().parents[2] / "dashboard"


class DashboardService:
    def __init__(self, bot: "StarCitizenHubBot", host: str = "0.0.0.0", port: int = 8080) -> None:
        self.bot = bot
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner: web.AppRunner | None = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.app.router.add_get("/", self.index)
        self.app.router.add_get("/api/overview", self.api_overview)
        self.app.router.add_get("/api/knowledge", self.api_knowledge)
        self.app.router.add_get("/api/events", self.api_events)
        self.app.router.add_get("/api/audit", self.api_audit)
        self.app.router.add_get("/api/config", self.api_config)
        self.app.router.add_static("/static", DASHBOARD_DIR, show_index=False)

    async def index(self, request: web.Request) -> web.Response:
        index_path = DASHBOARD_DIR / "index.html"
        if not index_path.exists():
            return web.Response(text="Dashboard not found.", status=404)
        return web.FileResponse(index_path)

    async def api_overview(self, request: web.Request) -> web.Response:
        entries = await self.bot.knowledge.list_entries()
        events = await self.bot.events.upcoming_events()
        return web.json_response({
            "guilds": len(self.bot.guilds),
            "knowledge_entries": len(entries),
            "upcoming_events": len(events),
            "latency_ms": round(self.bot.latency * 1000) if self.bot.latency else None,
            "user": str(self.bot.user) if self.bot.user else None,
        })

    async def api_knowledge(self, request: web.Request) -> web.Response:
        category = request.query.get("category")
        entries = await self.bot.knowledge.list_entries(category)
        return web.json_response({"entries": entries})

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
                }
                for event in events
            ]
        })

    async def api_audit(self, request: web.Request) -> web.Response:
        return web.json_response({"entries": [], "note": "Audit log integration coming soon."})

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
        })

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
