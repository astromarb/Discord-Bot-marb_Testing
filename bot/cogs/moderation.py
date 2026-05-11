from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.client import StarCitizenHubBot
from bot.services.message_service import resolve_text_channel
from bot.utils.formatters import make_embed, truncate


class ModerationCog(commands.Cog):
    def __init__(self, bot: StarCitizenHubBot) -> None:
        self.bot = bot

    def _log_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        return resolve_text_channel(guild, self.bot.config_data.get("server.admin_channel", "🔒admin-events-board"))

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if not self.bot.config_data.get("moderation.log_leaves", True):
            return
        channel = self._log_channel(member.guild)
        if channel:
            await channel.send(embed=make_embed("Member Left", f"{member} ({member.id})", color=0x795548))

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if not self.bot.config_data.get("moderation.log_message_deletions", True):
            return
        if not message.guild or message.author.bot:
            return
        channel = self._log_channel(message.guild)
        if channel:
            await channel.send(embed=make_embed("Message Deleted", f"Author: {message.author.mention}\nChannel: {message.channel.mention}\nContent: {truncate(message.content or '[no text content]')}", color=0xF44336))

    @app_commands.command(name="report", description="Report an issue to moderators.")
    @app_commands.describe(details="What happened? Include names, channels, or message links if useful.")
    async def report(self, interaction: discord.Interaction, details: str) -> None:
        if not interaction.guild:
            await interaction.response.send_message("This command only works in a server.", ephemeral=True)
            return
        channel = self._log_channel(interaction.guild)
        if channel:
            await channel.send(embed=make_embed("Member Report", f"From {interaction.user.mention}:\n{truncate(details)}", color=0xE91E63))
        await interaction.response.send_message("Report submitted to moderators.", ephemeral=True)


async def setup(bot: StarCitizenHubBot) -> None:
    await bot.add_cog(ModerationCog(bot))
