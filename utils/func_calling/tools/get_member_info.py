import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def get_member_info_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    user_id = params.get("user_id")

    try:
        member = await guild.fetch_member(int(user_id))
        if not member: return f"error: Member not found with ID {user_id}."

        roles = [role.name for role in member.roles if role.name != "@everyone"]
        joined_at = member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "Unknown"
        created_at = member.created_at.strftime("%Y-%m-%d %H:%M:%S") if member.created_at else "Unknown"

        info_str = (
            f"User Information for {member.display_name} (ID: {member.id}):\n"
            f"- Username: {member.name}#{member.discriminator}\n"
            f"- Created At: {created_at}\n"
            f"- Joined At: {joined_at}\n"
            f"- Roles: {', '.join(roles) if roles else 'None'}\n"
            f"- Administrator: {member.guild_permissions.administrator}\n"
            f"- Top Role: {member.top_role.name}"
        )
        logger.info(f"get_member_info_tool: Successfully fetched info for {member.display_name}.")
        return info_str
    except Exception as e:
        logger.error(f"Error fetching member info: {e}")
        return f"error: Failed to fetch member info: {e}"