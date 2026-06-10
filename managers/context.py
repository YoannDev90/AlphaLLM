"""Helpers to gather and format Discord server context.

Provides utilities to collect basic server metadata and format it for
inclusion in system prompts or logs.
"""

import discord

from utils.logger import get_logger

logger = get_logger()


async def get_server_context(guild: discord.Guild):
    """Gather context about the given Discord guild.

    Parameters
    ----------
    guild : discord.Guild
        Guild object to inspect.

    Returns
    -------
    dict
        A dictionary containing summarized server metadata suitable for
        inclusion in prompts (name, member list, emojis, roles, etc.).
    """
    # Essayer de récupérer les membres si le cache est vide
    if not guild.chunked and guild.member_count < 1000:
        try:
            await guild.chunk()
        except Exception:
            pass

    online_members = [
        m.display_name for m in guild.members if m.status != discord.Status.offline
    ]

    context = {
        "server_name": guild.name,
        "member_count": guild.member_count,
        "online_members": online_members[:30],
    }
    return context


def format_context_for_prompt(context: dict):
    """Convert the server context dict into a human-readable string.

    Parameters
    ----------
    context : dict
        Context dictionary returned by `get_server_context`.

    Returns
    -------
    str
        Multi-line string summarizing the server for model prompts.
    """
    lines = [
        f"Information about the current Discord server '{context['server_name']}':"
    ]
    if context.get("online_members"):
        lines.append(
            f"- Online members ({len(context['online_members'])}): {', '.join(context['online_members'])}"
        )
    else:
        lines.append(f"- Total member count: {context['member_count']}")

    return "\n".join(lines)
