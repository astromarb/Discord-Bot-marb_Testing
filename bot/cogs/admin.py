from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.client import StarCitizenHubBot
from bot.cogs.knowledge_base import moderator_only
from bot.services.message_service import resolve_text_channel
from bot.utils.formatters import make_embed


ANNOUNCEMENT_COLORS = {
    "paste_purple": 0xB39DDB,
    "cyan": 0x00BCD4,
    "orange": 0xFF9800,
    "teal": 0x009688,
}


class AdminCog(commands.Cog):
    admin_group = app_commands.Group(name="admin", description="Owner/admin bot controls")

    def __init__(self, bot: StarCitizenHubBot) -> None:
        self.bot = bot

    async def _channel_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        if not interaction.guild:
            return []
        channels = [ch for ch in interaction.guild.text_channels if current.lower() in ch.name.lower()]
        return [app_commands.Choice(name=ch.name, value=str(ch.id)) for ch in channels[:25]]

    @app_commands.command(name="announce", description="Send an announcement to a channel.")
    @moderator_only()
    @app_commands.describe(
        channel="Select target channel",
        title="Announcement title",
        message="Announcement text",
        color="Announcement color (default: paste_purple)",
    )
    @app_commands.autocomplete(channel=_channel_autocomplete)
    @app_commands.choices(color=[
        app_commands.Choice(name="Paste Purple", value="paste_purple"),
        app_commands.Choice(name="Cyan", value="cyan"),
        app_commands.Choice(name="Orange", value="orange"),
        app_commands.Choice(name="Teal", value="teal"),
    ])
    async def announce(
        self, interaction: discord.Interaction, channel: str, title: str, message: str, color: str = "paste_purple"
    ) -> None:
        if not interaction.guild:
            await interaction.response.send_message("This command only works in a server.", ephemeral=True)
            return
        try:
            target = interaction.guild.get_channel(int(channel))
        except (ValueError, TypeError):
            await interaction.response.send_message("Invalid channel selection.", ephemeral=True)
            return
        if not isinstance(target, discord.TextChannel):
            await interaction.response.send_message("Channel not found or is not a text channel.", ephemeral=True)
            return
        hex_color = ANNOUNCEMENT_COLORS.get(color, ANNOUNCEMENT_COLORS["paste_purple"])
        await target.send(embed=make_embed(title, message, color=hex_color))
        await interaction.response.send_message(f"Announcement sent to {target.mention}.", ephemeral=True)

    @app_commands.command(name="stats", description="Show bot status and content statistics.")
    @moderator_only()
    async def stats(self, interaction: discord.Interaction) -> None:
        entries = await self.bot.knowledge.list_entries()
        events = await self.bot.events.upcoming_events()
        text = f"Guilds: {len(self.bot.guilds)}\nKnowledge entries: {len(entries)}\nUpcoming events: {len(events)}\nLatency: {round(self.bot.latency * 1000)} ms"
        await interaction.response.send_message(embed=make_embed("Bot Stats", text), ephemeral=True)



async def setup(bot: StarCitizenHubBot) -> None:
    await bot.add_cog(AdminCog(bot))
