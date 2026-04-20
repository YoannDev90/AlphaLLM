"""Tool implementations for function calling."""

import datetime
import logging
from typing import Dict, List
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


async def execute_tool(func_name: str, params: Dict[str, str], guild=None) -> str:
    """Execute a tool function."""
    logger.info(f"Executing tool: {func_name} with params: {params}")
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
        case _:
            return f"Unknown function: {func_name}"
