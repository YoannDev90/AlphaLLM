import logging
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def create_channel_tool(params, guild=None):
    """
    Tool implementation for creating a Discord text channel.
    Expects 'guild' to be an instance of discord.Guild.
    """
    if not guild:
         logger.warning("create_channel_tool: Discord context missing (guild not provided)")
         return "error: Discord context missing (guild not provided)"

    channel_name = params.get("channel_name")
    category_id = params.get("category_id")
    topic = params.get("topic")

    if not channel_name:
        logger.warning("create_channel_tool: Missing 'channel_name' parameter")
        return "error: Missing 'channel_name' parameter"

    logger.info(f"create_channel_tool: Creating channel '{channel_name}' in guild '{guild.name}' (category: {category_id})")

    try:
        category = None
        if category_id:
            category = guild.get_channel(int(category_id))
            if not category:
                logger.warning(f"create_channel_tool: Category with ID {category_id} not found")
        
        new_channel = await guild.create_text_channel(
            name=channel_name, 
            category=category, 
            topic=topic
        )
        msg = f"Successfully created text channel: {new_channel.name} (ID: {new_channel.id})"
        logger.info(f"create_channel_tool: {msg}")
        return msg
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        return f"error: Failed to create channel: {e}"
