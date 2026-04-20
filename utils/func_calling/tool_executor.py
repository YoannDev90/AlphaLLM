"""Tool implementations for function calling."""

import datetime
import logging
from typing import Dict, List
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

class ToolExecContext:
    """Context object to pass necessary information to tools."""
    def __init__(self, bot=None, guild=None, user_id=None, channel_id=None, author=None):
        self.bot = bot
        self.guild = guild
        self.user_id = user_id
        self.channel_id = channel_id
        self.author = author
        self.timestamp = datetime.datetime.now()
        
        # Pre-calculated permissions
        self.bot_permissions = None
        if guild and guild.me:
            if channel_id:
                channel = guild.get_channel(int(channel_id))
                if channel:
                    self.bot_permissions = channel.permissions_for(guild.me)
            if not self.bot_permissions:
                self.bot_permissions = guild.me.guild_permissions

async def execute_tool(func_name: str, params: Dict[str, str], context: ToolExecContext) -> str:
    """Execute a tool function."""
    logger.info(f"Executing tool: {func_name} with params: {params}")
    
    # Inject context into params for tools that need it
    if context.user_id: params["user_id"] = str(context.user_id)
    if context.channel_id: params["channel_id"] = str(context.channel_id)

    guild = context.guild

    match func_name:
        case "generate_image":
            from utils.func_calling.tools.image_gen import image_gen_tool
            return await image_gen_tool(params)
        case "create_channel":
            from utils.func_calling.tools.create_channel import create_channel_tool
            return await create_channel_tool(params, guild=guild)
        case "kick_member":
            from utils.func_calling.tools.kick_member import kick_member_tool
            return await kick_member_tool(params, guild=guild)
        case "create_role":
            from utils.func_calling.tools.create_role import create_role_tool
            return await create_role_tool(params, guild=guild)
        case "ban_member":
            from utils.func_calling.tools.ban_member import ban_member_tool
            return await ban_member_tool(params, guild=guild)
        case "timeout_member":
            from utils.func_calling.tools.timeout_member import timeout_member_tool
            return await timeout_member_tool(params, guild=guild)
        case "bulk_delete":
            from utils.func_calling.tools.bulk_delete import bulk_delete_tool
            return await bulk_delete_tool(params, guild=guild)
        case "get_member_info":
            from utils.func_calling.tools.get_member_info import get_member_info_tool
            return await get_member_info_tool(params, guild=guild)
        case "edit_channel":
            from utils.func_calling.tools.edit_channel import edit_channel_tool
            return await edit_channel_tool(params, guild=guild)
        case "add_role":
            from utils.func_calling.tools.add_role import add_role_tool
            return await add_role_tool(params, guild=guild)
        case "remove_role":
            from utils.func_calling.tools.remove_role import remove_role_tool
            return await remove_role_tool(params, guild=guild)
        case "move_member":
            from utils.func_calling.tools.move_member import move_member_tool
            return await move_member_tool(params, guild=guild)
        case "set_reminder":
            from utils.func_calling.tools.set_reminder import set_reminder_tool
            return await set_reminder_tool(params, guild=guild)
        case "slowmode_channel":
            from utils.func_calling.tools.slowmode_channel import slowmode_channel_tool
            return await slowmode_channel_tool(params, guild=guild)
        case "lock_channel":
            from utils.func_calling.tools.lock_channel import lock_channel_tool
            return await lock_channel_tool(params, guild=guild)
        case "server_stats":
            from utils.func_calling.tools.server_stats import server_stats_tool
            return await server_stats_tool(params, guild=guild)
        case "check_permissions":
            from utils.func_calling.tools.check_permissions import check_permissions_tool
            return await check_permissions_tool(params, guild=guild)
        case "list_roles":
            from utils.func_calling.tools.list_roles import list_roles_tool
            return await list_roles_tool(params, guild=guild)
        case "clone_channel":
            from utils.func_calling.tools.clone_channel import clone_channel_tool
            return await clone_channel_tool(params, guild=guild)
        case _:
            return f"Unknown function: {func_name}"
