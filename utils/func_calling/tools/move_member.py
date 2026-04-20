import logging
import discord
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def move_member_tool(params, guild=None):
    if not guild: return "error: Discord context missing (guild not provided)"
    user_id = params.get("user_id")
    voice_id = params.get("voice_channel_id")

    try:
        member = await guild.fetch_member(int(user_id))
        if not member: return f"error: Member not found with ID {user_id}."

        voice_channel = guild.get_channel(int(voice_id))
        if not voice_channel: return f"error: Voice channel not found with ID {voice_id}."

        if not isinstance(voice_channel, discord.VoiceChannel):
             return "error: Target channel is not a voice channel."

        if not member.voice:
             return f"error: {member.display_name} is not connected to a voice channel."

        if not guild.me.permissions_in(voice_channel).move_members:
             return "error: I do not have the 'Move Members' permission in that voice channel."

        await member.move_to(voice_channel)
        msg = f"Successfully moved {member.display_name} to voice channel: {voice_channel.name}."
        logger.info(f"move_member_tool: {msg}")
        return msg
    except Exception as e:
        if "403 Forbidden" in str(e) or "50013" in str(e):
             return "error: Permission denied (403). I cannot move members to this channel."
        return f"error: Failed to move member: {e}"