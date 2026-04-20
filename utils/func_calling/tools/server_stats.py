import logging
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def server_stats_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"

    try:
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        members = guild.member_count
        boosts = guild.premium_subscription_count
        boost_level = guild.premium_tier
        
        info = (
            f"Server Statistics for {guild.name}:\n"
            f"- Members: {members}\n"
            f"- Boosts: {boosts} (Level {boost_level})\n"
            f"- Text Channels: {text_channels}\n"
            f"- Voice Channels: {voice_channels}\n"
            f"- Categories: {categories}\n"
            f"- Roles Count: {len(guild.roles)}"
        )
        logger.info(f"server_stats_tool: Fetched stats for {guild.name}.")
        return info
    except Exception as e:
        return f"error: Failed to fetch server stats: {e}"