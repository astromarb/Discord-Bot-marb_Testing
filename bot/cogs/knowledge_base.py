from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.client import StarCitizenHubBot
from bot.utils.formatters import make_embed, truncate


def moderator_only() -> app_commands.Check:
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        roles = interaction.client.config_data.get("permissions.moderator_roles", ["Moderator", "Admin"])
        return any(role.name in roles for role in interaction.user.roles) or interaction.user.guild_permissions.manage_guild
    return app_commands.check(predicate)


class KnowledgeBaseCog(commands.Cog):
    kb_group = app_commands.Group(name="kb", description="Moderator knowledge base tools")

    def __init__(self, bot: StarCitizenHubBot) -> None:
        self.bot = bot

    @app_commands.command(name="faq", description="Search the server knowledge base.")
    @app_commands.describe(query="What you want to search for")
    async def faq(self, interaction: discord.Interaction, query: str) -> None:
        threshold = float(self.bot.config_data.get("knowledge_base.min_confidence_threshold", 0.55))
        matches = await self.bot.knowledge.search(query, min_confidence=threshold)
        if not matches:
            await interaction.response.send_message("I do not have a strong answer for that yet. Try `/ask` to alert moderators.", ephemeral=True)
            return
        match = matches[0]
        embed = make_embed(match.question, f"{match.answer}\n\n*Category:* {match.category} | *Confidence:* {match.confidence:.2f}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ask", description="Ask a question; low-confidence questions are queued for moderators.")
    @app_commands.describe(question="Your Star Citizen or server question")
    async def ask(self, interaction: discord.Interaction, question: str) -> None:
        threshold = float(self.bot.config_data.get("knowledge_base.min_confidence_threshold", 0.55))
        matches = await self.bot.knowledge.search(question, min_confidence=threshold)
        if matches:
            match = matches[0]
            await interaction.response.send_message(embed=make_embed(match.question, match.answer))
            return
        if interaction.guild and interaction.channel:
            await self.bot.knowledge.record_unanswered(question, interaction.user.id, interaction.channel.id)
            admin_channel_name = self.bot.config_data.get("server.admin_channel", "🔒admin-events-board")
            admin = discord.utils.get(interaction.guild.text_channels, name=admin_channel_name)
            if admin:
                await admin.send(embed=make_embed("Unanswered Question", f"From {interaction.user.mention} in {interaction.channel.mention}:\n{truncate(question)}", color=0xFF9800))
        await interaction.response.send_message("I do not know that yet. I queued it for moderators.", ephemeral=True)

    @kb_group.command(name="add", description="Add a knowledge base entry.")
    @moderator_only()
    @app_commands.describe(category="Category name", question="Question text", answer="Answer text", keywords="Comma-separated keywords")
    async def kb_add(self, interaction: discord.Interaction, category: str, question: str, answer: str, keywords: str) -> None:
        entry_id = await self.bot.knowledge.add_entry(category, question, answer, [item.strip() for item in keywords.split(",")])
        await interaction.response.send_message(f"Knowledge entry added: `{entry_id}`", ephemeral=True)

    @kb_group.command(name="list", description="List knowledge base entries.")
    @moderator_only()
    async def kb_list(self, interaction: discord.Interaction, category: str | None = None) -> None:
        entries = await self.bot.knowledge.list_entries(category)
        if not entries:
            await interaction.response.send_message("No entries found.", ephemeral=True)
            return
        lines = [f"`{row['id']}` — **{row['category']}** — {row['question']}" for row in entries[:20]]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @kb_group.command(name="delete", description="Delete a knowledge base entry by id.")
    @moderator_only()
    async def kb_delete(self, interaction: discord.Interaction, entry_id: str) -> None:
        removed = await self.bot.knowledge.delete_entry(entry_id)
        await interaction.response.send_message("Deleted." if removed else "Entry not found.", ephemeral=True)


async def setup(bot: StarCitizenHubBot) -> None:
    await bot.add_cog(KnowledgeBaseCog(bot))
