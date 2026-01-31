import logging

import discord

from bots.bot import bot as main_bot
from config import DEV_IDS, LOGGER_NAME
from utils.database.server_conf import (add_to_allowed_channels,
                                        add_to_allowed_roles)

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(
        name="whitelist_all",
        description="Whitelist all channels and roles of all servers",
    )
    async def whitelist_all(interaction: discord.Interaction):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message(
                "❌ You are not authorized to use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(
            f"Command /whitelist_all executed by {interaction.user.display_name}"
        )

        if not main_bot.guilds:
            await interaction.followup.send(
                "Le bot n'est présent dans aucun serveur.", ephemeral=True
            )
            return

        total_guilds = len(main_bot.guilds)
        updated_guilds = 0

        for guild in main_bot.guilds:
            try:
                # Whitelist all channels
                for channel in guild.channels:
                    await add_to_allowed_channels(guild.id, channel.id)

                # Whitelist all roles
                for role in guild.roles:
                    await add_to_allowed_roles(guild.id, role.id)

                updated_guilds += 1
                logger.info(
                    f"Whitelist mis à jour pour le serveur {guild.name} ({guild.id})"
                )

            except Exception as e:
                logger.error(f"Error updating server {guild.name}: {e}")

        await interaction.followup.send(
            f"Whitelist updated for {updated_guilds}/{total_guilds} servers.",
            ephemeral=True,
        )
