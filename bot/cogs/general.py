from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.client import StarCitizenHubBot
from bot.utils.formatters import make_embed, truncate


class GeneralCog(commands.Cog):
    def __init__(self, bot: StarCitizenHubBot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot response time.")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Pong. Latency: {round(self.bot.latency * 1000)} ms", ephemeral=True)

    @app_commands.command(name="serverinfo", description="Show basic server information.")
    async def serverinfo(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command only works in a server.", ephemeral=True)
            return
        embed = make_embed(
            "Server Information",
            f"**Name:** {guild.name}\n**Members:** {guild.member_count}\n**Channels:** {len(guild.channels)}",
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Show available StarCitizen Hub commands.")
    async def help(self, interaction: discord.Interaction) -> None:
        text = (
            "**Member commands**\n"
            "`/faq query:<text>` — search the knowledge base\n"
            "`/ask question:<text>` — ask a Star Citizen/server question\n"
            "`/events` — list upcoming events\n"
            "`/suggest idea:<text>` — send a suggestion to staff\n"
            "`/serverinfo` — show server stats\n"
            "`/ping` — check latency\n\n"
            "**Moderator commands**\n"
            "`/kb add`, `/kb list`, `/kb delete`\n"
            "`/event add`, `/event delete`, `/event list`\n"
            "`/announce`, `/stats`, `/admin reload`"
        )
        await interaction.response.send_message(embed=make_embed("StarCitizen Hub Help", text), ephemeral=True)

    @app_commands.command(name="suggest", description="Submit a server suggestion to moderators.")
    @app_commands.describe(idea="Your suggestion")
    async def suggest(self, interaction: discord.Interaction, idea: str) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command only works in a server.", ephemeral=True)
            return
        admin_channel_name = self.bot.config_data.get("server.admin_channel", "🔒admin-events-board")
        admin = discord.utils.get(guild.text_channels, name=admin_channel_name)
        if admin:
            await admin.send(embed=make_embed("New Suggestion", f"From {interaction.user.mention}:\n{truncate(idea)}", color=0xFFC107))
        await interaction.response.send_message("Suggestion submitted.", ephemeral=True)


async def setup(bot: StarCitizenHubBot) -> None:
    await bot.add_cog(GeneralCog(bot))
