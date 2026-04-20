import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def remove_role_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    user_id = params.get("user_id")
    role_id = params.get("role_id")

    try:
        member = await guild.fetch_member(int(user_id))
        if not member: return f"error: Member not found with ID {user_id}."

        role = guild.get_role(int(role_id))
        if not role: return f"error: Role not found with ID {role_id}."

        # Check hierarchy
        if guild.me.top_role <= role:
             return f"error: Cannot remove role '{role.name}'. My role is lower than or equal to that role in the Discord hierarchy."

        await member.remove_roles(role)
        msg = f"Successfully removed role '{role.name}' from {member.display_name}."
        logger.info(f"remove_role_tool: {msg}")
        return msg
    except Exception as e:
        if "403 Forbidden" in str(e) or "50013" in str(e):
             return "error: Permission denied (403). I do not have the 'Manage Roles' permission or the role is higher than mine."
        return f"error: Failed to remove role: {e}"