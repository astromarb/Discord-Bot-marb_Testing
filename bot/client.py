from __future__ import annotations

import logging

import discord
from discord.ext import commands

from bot.config import BotConfig, DATA_DIR
from bot.services.dashboard_service import DashboardService
from bot.services.event_service import EventService
from bot.services.knowledge_service import KnowledgeService

COGS = (
    "bot.cogs.general",
    "bot.cogs.knowledge_base",
    "bot.cogs.events_scheduler",
    "bot.cogs.onboarding",
    "bot.cogs.engagement",
    "bot.cogs.moderation",
    "bot.cogs.admin",
)


class StarCitizenHubBot(commands.Bot):
    def __init__(self, config: BotConfig) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        intents.dm_messages = True
        intents.message_content = bool(config.get("discord_intents.message_content", True))
        intents.members = bool(config.get("discord_intents.members", True))
        intents.reactions = True

        super().__init__(command_prefix=config.get("bot.prefix", "!"), intents=intents, help_command=None)
        self.config_data = config
        self.knowledge = KnowledgeService(DATA_DIR / "knowledge_base.json")
        self.events = EventService(DATA_DIR / "events.json")
        self.dashboard = DashboardService(
            self,
            host=config.get("dashboard.host", "0.0.0.0"),
            port=int(config.get("dashboard.port", 8080)),
        )
        self.log = logging.getLogger("starcitizen_hub.bot")

    async def setup_hook(self) -> None:
        for extension in COGS:
            await self.load_extension(extension)
            self.log.info("Loaded extension %s", extension)

        if self.config_data.guild_id:
            guild = discord.Object(id=self.config_data.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            self.log.info("Synced %s slash commands to guild %s", len(synced), self.config_data.guild_id)
        else:
            synced = await self.tree.sync()
            self.log.info("Synced %s global slash commands", len(synced))

        if self.config_data.get("dashboard.enabled", True):
            await self.dashboard.start()

    async def on_ready(self) -> None:
        activity_text = self.config_data.get("bot.activity", "Watching the Verse")
        await self.change_presence(activity=discord.Game(name=activity_text))
        self.log.info("Logged in as %s", self.user)

    async def close(self) -> None:
        await self.dashboard.stop()
        await super().close()
