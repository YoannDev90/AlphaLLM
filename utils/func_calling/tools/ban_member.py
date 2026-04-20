import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def ban_member_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    user_id = params.get("user_id")
    reason = params.get("reason", "No reason provided")
    delete_days = int(params.get("delete_message_days", 1))

    try:
        member = await guild.fetch_member(int(user_id))
        if member:
            # Check hierarchy
            if guild.me.top_role <= member.top_role:
                 return f"error: Cannot ban {member.display_name}. My role ({guild.me.top_role.name}) is lower or equal than theirs ({member.top_role.name}) in Discord hierarchy."
            if member == guild.owner:
                 return "error: Cannot ban the server owner."
        
        await guild.ban(discord.Object(id=int(user_id)), reason=reason, delete_message_days=delete_days)
        msg = f"Successfully banned user ID {user_id} and deleted {delete_days} days of messages."
        logger.info(f"ban_member_tool: {msg}")
        return msg
    except Exception as e:
        if "403 Forbidden" in str(e) or "50013" in str(e):
             return "error: Permission denied (403). I do not have the 'Ban Members' permission or the target's role is higher than mine."
        return f"error: Failed to ban: {e}"