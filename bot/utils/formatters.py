from __future__ import annotations

import discord


def make_embed(title: str, description: str, *, color: int = 0x4CAF50) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="𝘕𝘦𝘹𝘶𝘴 𝘈𝘐")
    return embed


def truncate(text: str, limit: int = 1900) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
