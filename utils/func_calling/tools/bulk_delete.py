import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def bulk_delete_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    amount = int(params.get("amount", 1))
    channel_id = params.get("channel_id")

    try:
        # Default to current channel (bot loop might need more context if channel_id is not passed)
        # For now, if channel_id is not provided, we need the channel context from the executor
        # We'll assume the executor passes the active channel if needed, or we search by ID
        channel = None
        if channel_id:
            channel = guild.get_channel(int(channel_id))
        
        if not channel:
            return "error: Channel not found or not provided."

        if not isinstance(channel, discord.TextChannel):
            return "error: Target channel must be a text channel."

        if not guild.me.permissions_in(channel).manage_messages:
            return "error: I do not have the 'Manage Messages' permission in that channel."

        deleted = await channel.purge(limit=amount)
        msg = f"Successfully deleted {len(deleted)} messages in {channel.name}."
        logger.info(f"bulk_delete_tool: {msg}")
        return msg
    except Exception as e:
        if "403 Forbidden" in str(e) or "50013" in str(e):
             return "error: Permission denied (403). I cannot delete messages in this channel."
        return f"error: Failed to bulk delete: {e}"