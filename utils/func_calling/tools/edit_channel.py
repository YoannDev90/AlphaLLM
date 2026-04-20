import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def edit_channel_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    channel_id = params.get("channel_id")
    new_name = params.get("new_name")
    new_topic = params.get("new_topic")

    try:
        channel = guild.get_channel(int(channel_id))
        if not channel: return f"error: Channel not found with ID {channel_id}."

        updates = {}
        if new_name: updates["name"] = new_name
        if new_topic: updates["topic"] = new_topic

        if not updates:
            return "error: No updates specified (new_name or new_topic required)."

        if not guild.me.permissions_in(channel).manage_channels:
            return "error: I do not have the 'Manage Channels' permission in that channel."

        await channel.edit(**updates)
        msg = f"Successfully updated channel {channel.name} (ID: {channel.id})."
        logger.info(f"edit_channel_tool: {msg}")
        return msg
    except Exception as e:
        if "403 Forbidden" in str(e) or "50013" in str(e):
             return "error: Permission denied (403). I cannot edit this channel."
        return f"error: Failed to edit channel: {e}"