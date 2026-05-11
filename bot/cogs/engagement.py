from __future__ import annotations

import itertools

from discord.ext import commands, tasks

from bot.client import StarCitizenHubBot
from bot.services.message_service import resolve_text_channel
from bot.utils.formatters import make_embed

FACTS = [
    "Cargo discipline wins operations: label roles, assign loaders, and confirm destination before takeoff.",
    "For new pilots, a crew role can be safer and more profitable than flying solo immediately.",
    "Before an event, confirm spawn point, medical supplies, tractor beams, and cargo grid space.",
]
PROMPTS = [
    "What gameplay loop should we train as a group next: hauling, mining, salvage, combat, or exploration?",
    "What ship or role do you want to learn this week?",
    "What is one server resource that would make onboarding easier?",
]


class EngagementCog(commands.Cog):
    def __init__(self, bot: StarCitizenHubBot) -> None:
        self.bot = bot
        self._facts = itertools.cycle(FACTS)
        self._prompts = itertools.cycle(PROMPTS)
        self.fun_fact_loop.change_interval(hours=float(bot.config_data.get("engagement.fun_facts_interval_hours", 3)))
        self.fun_fact_loop.start()
        self.prompt_loop.start()

    def cog_unload(self) -> None:
        self.fun_fact_loop.cancel()
        self.prompt_loop.cancel()

    @tasks.loop(hours=3)
    async def fun_fact_loop(self) -> None:
        for guild in self.bot.guilds:
            channel = resolve_text_channel(guild, self.bot.config_data.get("engagement.fun_facts_channel", "fun-facts"))
            if channel:
                await channel.send(embed=make_embed("Verse Tip", next(self._facts), color=0x607D8B))

    @tasks.loop(hours=168)
    async def prompt_loop(self) -> None:
        for guild in self.bot.guilds:
            channel = resolve_text_channel(guild, self.bot.config_data.get("server.general_channel", "general"))
            if channel:
                await channel.send(embed=make_embed("Discussion Prompt", next(self._prompts), color=0x9C27B0))

    @fun_fact_loop.before_loop
    @prompt_loop.before_loop
    async def before_loops(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: StarCitizenHubBot) -> None:
    await bot.add_cog(EngagementCog(bot))
