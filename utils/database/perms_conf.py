from utils.database.db_manager import db_manager
from datetime import datetime
import logging
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def get_blacklist():
    return await db_manager.get_blacklist()

async def blacklist_add(user_id: int, reason: str):
    return await db_manager.blacklist_add(user_id, reason)

async def blacklist_remove(user_id: int):
    return await db_manager.blacklist_remove(user_id)
    
async def get_allowed_channels(guild_id):
    return await db_manager.get_allowed_channels(guild_id)
    
async def get_allowed_roles(guild_id):
    return await db_manager.get_allowed_roles(guild_id)