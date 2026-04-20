import logging
from datetime import timedelta
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def timeout_member_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    user_id = params.get("user_id")
    duration_min = int(params.get("duration_minutes", 10))
    reason = params.get("reason", "No reason provided")

    try:
        member = await guild.fetch_member(int(user_id))
        if not member:
            return f"error: Member not found with ID {user_id}."
        
        # Check hierarchy
        if guild.me.top_role <= member.top_role:
             return f"error: Cannot timeout {member.display_name}. My role ({guild.me.top_role.name}) is lower or equal than theirs ({member.top_role.name}) in Discord hierarchy."
        if member == guild.owner:
             return "error: Cannot timeout the server owner."

        # Timeout using timedelta
        duration = timedelta(minutes=duration_min)
        await member.timeout(duration, reason=reason)
        
        msg = f"Successfully timed out member: {member.display_name} (ID: {member.id}) for {duration_min} minutes."
        logger.info(f"timeout_member_tool: {msg}")
        return msg
    except Exception as e:
        if "403 Forbidden" in str(e) or "50013" in str(e):
             return "error: Permission denied (403). I do not have the 'Moderate Members' permission or the target's role is higher than mine."
        return f"error: Failed to timeout: {e}"