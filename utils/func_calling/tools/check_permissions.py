import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def check_permissions_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    user_id = params.get("user_id")
    channel_id = params.get("channel_id")

    try:
        member = await guild.fetch_member(int(user_id)) if user_id else guild.me
        channel = guild.get_channel(int(channel_id)) if channel_id else None
        
        if not member: return "error: Member not found."
        
        perms = member.guild_permissions
        if channel:
            perms = member.permissions_in(channel)
        
        # Select common/important permissions to check
        relevant_perms = [
            'administrator', 'manage_guild', 'manage_roles', 'manage_channels',
            'kick_members', 'ban_members', 'send_messages', 'manage_messages',
            'move_members', 'moderate_members'
        ]
        
        active_perms = [p.replace('_', ' ').title() for p, v in perms if p in relevant_perms and v]
        
        location = f"in {channel.name}" if channel else "globally in the server"
        msg = f"Permissions for {member.display_name} {location}:\n"
        msg += ", ".join(active_perms) if active_perms else "None of the standard moderation permissions."
        
        logger.info(f"check_permissions_tool: Checked perms for {member.display_name} {location}.")
        return msg
    except Exception as e:
        return f"error: Failed to check permissions: {e}"