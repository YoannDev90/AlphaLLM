import logging
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def kick_member_tool(params, guild=None):
    """
    Tool implementation for kicking a member from a Discord server.
    Expects 'guild' to be an instance of discord.Guild.
    """
    if not guild:
         logger.warning("kick_member_tool: Discord context missing (guild not provided)")
         return "error: Discord context missing (guild not provided)"

    user_id = params.get("user_id")
    # For some reason user_id could be a string if it's from the LLM or an int
    # if it was already processed.
    if not user_id:
        logger.warning("kick_member_tool: Missing 'user_id' parameter")
        return "error: Missing 'user_id' parameter"

    reason = params.get("reason", "No reason provided")
    logger.info(f"kick_member_tool: Attempting to kick user {user_id} from guild '{guild.name}' for reason: {reason}")

    try:
        # Récupération directe via l'API (plus fiable que le cache)
        logger.info(f"kick_member_tool: Fetching member {user_id} directly from Discord API...")
        member = await guild.fetch_member(int(user_id))

        if not member:
            logger.warning(f"kick_member_tool: Member not found with ID {user_id}")
            return f"error: Member not found with ID {user_id}."

        await member.kick(reason=reason)
        msg = f"Successfully kicked member: {member.display_name} (ID: {member.id})"
        logger.info(f"kick_member_tool: {msg}")
        return msg
    except Exception as e:
        logger.error(f"Error kicking member: {e}")
        if "403 Forbidden" in str(e) or "50013" in str(e):
            # Precise identification of the cause
            if member and guild.me.top_role <= member.top_role:
                error_msg = f"error: Cannot kick {member.display_name}. My role ({guild.me.top_role.name}) is lower than or equal to theirs ({member.top_role.name}) in the Discord hierarchy."
            elif not guild.me.guild_permissions.kick_members:
                error_msg = "error: I do not have the 'Kick Members' permission in my role settings."
            elif member and member == guild.owner:
                error_msg = "error: Cannot kick the server owner."
            else:
                error_msg = "error: Permission denied (403). Please check my role position and 'Kick Members' permissions."
            
            logger.warning(f"kick_member_tool: {error_msg}")
            return error_msg
        return f"error: Failed to kick member: {e}"
