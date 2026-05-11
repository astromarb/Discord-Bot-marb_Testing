from __future__ import annotations

import discord


def resolve_text_channel(guild: discord.Guild, name_or_mention: str | None) -> discord.TextChannel | None:
    if not name_or_mention:
        return None
    cleaned = name_or_mention.strip().replace("#", "")
    if cleaned.startswith("<") and cleaned.endswith(">"):
        cleaned = cleaned.strip("<#>")
        return guild.get_channel(int(cleaned)) if cleaned.isdigit() else None
    for channel in guild.text_channels:
        if channel.name == cleaned:
            return channel
    return None


def has_any_role(member: discord.Member, role_names: list[str]) -> bool:
    wanted = {name.lower() for name in role_names}
    return any(role.name.lower() in wanted for role in member.roles)
