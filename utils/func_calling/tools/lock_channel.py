import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def lock_channel_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    lock = params.get("lock", True)
    channel_id = params.get("channel_id")

    try:
        channel = guild.get_channel(int(channel_id)) if channel_id else None
        if not channel: return "error: Channel not found or not provided."
        
        if not isinstance(channel, discord.TextChannel):
            return "error: Locking is for text channels."

        if not guild.me.permissions_in(channel).manage_roles:
            return "error: I do not have 'Manage Roles' (permissions) in this channel."

        everyone_role = guild.default_role
        overwrites = channel.overwrites_for(everyone_role)
        
        if lock:
            overwrites.send_messages = False
            msg = f"Successfully locked channel {channel.name}."
        else:
            overwrites.send_messages = True
            msg = f"Successfully unlocked channel {channel.name}."

        await channel.set_permissions(everyone_role, overwrite=overwrites)
        logger.info(f"lock_channel_tool: {msg}")
        return msg
    except Exception as e:
        if "403 Forbidden" in str(e) or "50013" in str(e):
             return "error: Permission denied (403). I cannot manage permissions in this channel."
        return f"error: Failed to lock channel: {e}"