import logging
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def list_roles_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"

    try:
        # Sort roles by position (highest first)
        sorted_roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
        
        role_list = "List of server roles (highest to lowest):\n"
        for role in sorted_roles:
            if role.name == "@everyone": continue
            role_list += f"- {role.name} (ID: {role.id}) - Members: {len(role.members)}\n"
        
        logger.info(f"list_roles_tool: Listed {len(guild.roles)} roles for {guild.name}.")
        return role_list
    except Exception as e:
        return f"error: Failed to list roles: {e}"