from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from bot.client import StarCitizenHubBot
from bot.services.message_service import resolve_text_channel
from bot.utils.formatters import make_embed

ROLE_EMOJIS = {
    "🚀": "Combat/PvP",
    "⛏️": "Mining",
    "📦": "Trading/Hauling",
    "🎭": "Roleplay",
    "🛠️": "Engineering/Crafting",
    "📰": "News/Updates",
    "🎮": "General Gaming",
}


class OnboardingCog(commands.Cog):
    def __init__(self, bot: StarCitizenHubBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if not self.bot.config_data.get("onboarding.enabled", True):
            return
        rules_channel = resolve_text_channel(member.guild, self.bot.config_data.get("server.rules_channel", "rules"))
        description = (
            f"Welcome to **{member.guild.name}**. Read the rules"
            f"{f' in {rules_channel.mention}' if rules_channel else ''}, then choose interests below."
        )
        try:
            dm = await member.send(embed=make_embed("Welcome to the Nexus Nebula", description))
            for emoji in ROLE_EMOJIS:
                await dm.add_reaction(emoji)
        except discord.Forbidden:
            channel = resolve_text_channel(member.guild, self.bot.config_data.get("server.welcome_channel", "welcome"))
            if channel:
                await channel.send(f"Welcome {member.mention}. I could not DM you, so check the rules and onboarding channels.")
        asyncio.create_task(self._followup(member))

    async def _followup(self, member: discord.Member) -> None:
        hours = int(self.bot.config_data.get("onboarding.followup_dm_hours", 24))
        await asyncio.sleep(hours * 3600)
        try:
            await member.send(embed=make_embed("How is your first day going?", "Introduce yourself, ask for a crew role, or check `/events` for the next group activity."))
        except discord.Forbidden:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is not None or payload.user_id == self.bot.user.id:
            return
        role_name = ROLE_EMOJIS.get(str(payload.emoji))
        if not role_name:
            return
        for guild in self.bot.guilds:
            member = guild.get_member(payload.user_id)
            if not member:
                continue
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.add_roles(role, reason="Onboarding interest selection")
                try:
                    await member.send(f"Assigned role: {role.name}")
                except discord.Forbidden:
                    pass
            break


async def setup(bot: StarCitizenHubBot) -> None:
    await bot.add_cog(OnboardingCog(bot))
