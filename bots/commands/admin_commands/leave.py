import logging

import discord

from bots.bot import bot as main_bot
from config import DEV_IDS, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(name="leave", description="Make the bot leave a server")
    async def leave(interaction: discord.Interaction, guild_id: str):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message(
                "❌ You are not authorized to use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(
            f"Command /leave executed by {interaction.user.display_name} for server {guild_id}"
        )

        if not guild_id.isdigit() or int(guild_id) <= 0:
            await interaction.followup.send(
                "The provided server ID is invalid.", ephemeral=True
            )
            return

        guild = main_bot.get_guild(int(guild_id))
        if guild is None:
            await interaction.followup.send(
                "The bot is not present in this server or the ID is incorrect.",
                ephemeral=True,
            )
            return

        try:
            await guild.leave()
            await interaction.followup.send(
                f"The bot has left the server **{guild.name}** (ID: `{guild_id}`).",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            logger.error(f"HTTP error when attempting to leave server {guild_id}: {e}")
            await interaction.followup.send(
                "Error when attempting to leave the server. Please try again later.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error when attempting to leave server {guild_id}: {e}"
            )
            await interaction.followup.send(
                "Unexpected error. Please try again later.", ephemeral=True
            )
