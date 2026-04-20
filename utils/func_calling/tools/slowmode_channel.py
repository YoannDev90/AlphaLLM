import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def slowmode_channel_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    seconds = int(params.get("seconds", 0))
    channel_id = params.get("channel_id")

    try:
        channel = guild.get_channel(int(channel_id)) if channel_id else None
        if not channel: return "error: Channel not found or not provided."
        
        if not isinstance(channel, discord.TextChannel):
            return "error: Slowmode can only be applied to text channels."

        if not guild.me.permissions_in(channel).manage_channels:
            return "error: I do not have 'Manage Channels' permission in this channel."

        await channel.edit(slowmode_delay=seconds)
        msg = f"Successfully set slowmode to {seconds} seconds for channel {channel.name}."
        logger.info(f"slowmode_channel_tool: {msg}")
        return msg
    except Exception as e:
        if "403 Forbidden" in str(e) or "50013" in str(e):
             return "error: Permission denied (403). I cannot edit this channel settings."
        return f"error: Failed to set slowmode: {e}"