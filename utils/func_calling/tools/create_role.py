import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def create_role_tool(params, guild=None):
    """
    Tool implementation for creating a Discord role.
    Expects 'guild' to be an instance of discord.Guild.
    """
    if not guild:
         logger.warning("create_role_tool: Discord context missing (guild not provided)")
         return "error: Discord context missing (guild not provided)"

    role_name = params.get("role_name")
    color_hex = params.get("color")
    hoist = params.get("hoist", False)
    reason = params.get("reason", "No reason provided")

    if not role_name:
        logger.warning("create_role_tool: Missing 'role_name' parameter")
        return "error: Missing 'role_name' parameter"

    logger.info(f"create_role_tool: Creating role '{role_name}' in guild '{guild.name}' (color: {color_hex}, hoist: {hoist})")

    try:
        # Permission check
        if not guild.me.guild_permissions.manage_roles:
            error_msg = "error: I do not have the 'Manage Roles' permission in this server."
            logger.warning(f"create_role_tool: {error_msg}")
            return error_msg

        # Color handling
        role_color = discord.Color.default()
        if color_hex:
            try:
                # Handle both #FFFFFF and 0xFFFFFF formats
                clean_color = color_hex.lstrip('#').replace('0x', '')
                role_color = discord.Color(int(clean_color, 16))
            except Exception as color_err:
                logger.warning(f"create_role_tool: Invalid color hex provided '{color_hex}', using default: {color_err}")

        # Task: Create role
        new_role = await guild.create_role(
            name=role_name,
            color=role_color,
            hoist=hoist,
            reason=reason
        )

        msg = f"Successfully created role: {new_role.name} (ID: {new_role.id}) with color {role_color}"
        logger.info(f"create_role_tool: {msg}")
        return msg

    except Exception as e:
        logger.error(f"Error creating role: {e}")
        if "403 Forbidden" in str(e) or "50013" in str(e):
             error_msg = "error: Permission denied (403). I cannot create roles. Check my 'Manage Roles' permissions."
             logger.warning(f"create_role_tool: {error_msg}")
             return error_msg
        return f"error: Failed to create role: {e}"