from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.client import StarCitizenHubBot
from bot.cogs.knowledge_base import moderator_only
from bot.services.message_service import resolve_text_channel
from bot.utils.formatters import make_embed


class AdminCog(commands.Cog):
    admin_group = app_commands.Group(name="admin", description="Owner/admin bot controls")

    def __init__(self, bot: StarCitizenHubBot) -> None:
        self.bot = bot

    @app_commands.command(name="announce", description="Send an announcement to a named channel.")
    @moderator_only()
    @app_commands.describe(channel="Target channel name", message="Announcement text")
    async def announce(self, interaction: discord.Interaction, channel: str, message: str) -> None:
        if not interaction.guild:
            await interaction.response.send_message("This command only works in a server.", ephemeral=True)
            return
        target = resolve_text_channel(interaction.guild, channel)
        if not target:
            await interaction.response.send_message("Channel not found.", ephemeral=True)
            return
        await target.send(embed=make_embed("Announcement", message, color=0x00BCD4))
        await interaction.response.send_message(f"Announcement sent to {target.mention}.", ephemeral=True)

    @app_commands.command(name="stats", description="Show bot status and content statistics.")
    @moderator_only()
    async def stats(self, interaction: discord.Interaction) -> None:
        entries = await self.bot.knowledge.list_entries()
        events = await self.bot.events.upcoming_events()
        text = f"Guilds: {len(self.bot.guilds)}\nKnowledge entries: {len(entries)}\nUpcoming events: {len(events)}\nLatency: {round(self.bot.latency * 1000)} ms"
        await interaction.response.send_message(embed=make_embed("Bot Stats", text), ephemeral=True)

    @admin_group.command(name="reload", description="Explain reload behavior for local files and live data.")
    @moderator_only()
    async def admin_reload(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Config files are read at startup. Restart the bot process after file edits. KB/events update live through commands.", ephemeral=True)

    @admin_group.command(name="shutdown", description="Shut down the bot process. Owner only.")
    async def admin_shutdown(self, interaction: discord.Interaction, reason: str | None = None) -> None:
        if not interaction.guild or interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("Only the server owner can shut down the bot.", ephemeral=True)
            return
        await interaction.response.send_message(f"Shutting down. Reason: {reason or 'not specified'}", ephemeral=True)
        await self.bot.close()


async def setup(bot: StarCitizenHubBot) -> None:
    await bot.add_cog(AdminCog(bot))
