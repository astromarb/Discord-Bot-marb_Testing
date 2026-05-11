from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot.client import StarCitizenHubBot
from bot.cogs.knowledge_base import moderator_only
from bot.services.message_service import resolve_text_channel
from bot.utils.formatters import make_embed
from bot.utils.validators import parse_datetime


class EventsCog(commands.Cog):
    event_group = app_commands.Group(name="event", description="Moderator event management tools")

    def __init__(self, bot: StarCitizenHubBot) -> None:
        self.bot = bot
        self.reminder_loop.start()

    def cog_unload(self) -> None:
        self.reminder_loop.cancel()

    @app_commands.command(name="events", description="List upcoming community events.")
    async def events(self, interaction: discord.Interaction) -> None:
        events = await self.bot.events.upcoming_events()
        if not events:
            await interaction.response.send_message("No upcoming events are scheduled yet.", ephemeral=True)
            return
        lines = [f"**{event.title}** — <t:{int(event.starts_at.timestamp())}:F>\n{event.description}\nID: `{event.id}`" for event in events]
        await interaction.response.send_message(embed=make_embed("Upcoming Events", "\n\n".join(lines)))

    @event_group.command(name="add", description="Create a community event.")
    @moderator_only()
    @app_commands.describe(
        title="Event title",
        description="Event description",
        starts_at="ISO datetime, e.g. 2026-05-10T20:00:00-05:00",
        channel="Target channel name, e.g. events-announcements",
        reminders="Comma-separated reminder hours, e.g. 24,2",
    )
    async def event_add(self, interaction: discord.Interaction, title: str, description: str, starts_at: str, channel: str | None = None, reminders: str = "24,2") -> None:
        try:
            parsed = parse_datetime(starts_at)
            reminder_hours = [int(item.strip()) for item in reminders.split(",") if item.strip()]
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        event_id = await self.bot.events.add_event(title, description, parsed, channel, reminder_hours)
        await interaction.response.send_message(f"Event created: `{event_id}`", ephemeral=True)

    @event_group.command(name="delete", description="Delete an event by id.")
    @moderator_only()
    async def event_delete(self, interaction: discord.Interaction, event_id: str) -> None:
        removed = await self.bot.events.delete_event(event_id)
        await interaction.response.send_message("Deleted." if removed else "Event not found.", ephemeral=True)

    @event_group.command(name="list", description="List upcoming events with ids.")
    @moderator_only()
    async def event_list(self, interaction: discord.Interaction) -> None:
        events = await self.bot.events.upcoming_events(limit=25)
        if not events:
            await interaction.response.send_message("No upcoming events.", ephemeral=True)
            return
        lines = [f"`{event.id}` — **{event.title}** — <t:{int(event.starts_at.timestamp())}:F>" for event in events]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @tasks.loop(minutes=5)
    async def reminder_loop(self) -> None:
        for guild in self.bot.guilds:
            due = await self.bot.events.due_reminders()
            for event, hours_before in due:
                target = resolve_text_channel(guild, event.channel_target) or resolve_text_channel(guild, self.bot.config_data.get("events.announcement_channel"))
                if target:
                    await target.send(embed=make_embed(f"Event Reminder: {event.title}", f"{event.description}\n\nStarts <t:{int(event.starts_at.timestamp())}:R>.", color=0x2196F3))
                    await self.bot.events.mark_reminder_sent(event.id, hours_before)

    @reminder_loop.before_loop
    async def before_reminder_loop(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: StarCitizenHubBot) -> None:
    await bot.add_cog(EventsCog(bot))
