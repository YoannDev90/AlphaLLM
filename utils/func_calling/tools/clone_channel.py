import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def clone_channel_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    channel_id = params.get("channel_id")
    new_name = params.get("new_name")
    delete_original = params.get("delete_original", False)

    try:
        channel = guild.get_channel(int(channel_id))
        if not channel: return f"error: Channel not found with ID {channel_id}."

        if not guild.me.permissions_in(channel).manage_channels:
            return "error: I do not have 'Manage Channels' permission in this channel."

        cloned = await channel.clone(name=new_name if new_name else f"{channel.name}-cloned")
        
        msg = f"Successfully cloned channel {channel.name} to {cloned.name} (ID: {cloned.id})."
        
        if delete_original:
            await channel.delete(reason="Cloned and original deleted by tool.")
            msg += " Original channel has been deleted."
            
        logger.info(f"clone_channel_tool: {msg}")
        return msg
    except Exception as e:
        if "403 Forbidden" in str(e) or "50013" in str(e):
             return "error: Permission denied (403). I cannot clone this channel."
        return f"error: Failed to clone channel: {e}"