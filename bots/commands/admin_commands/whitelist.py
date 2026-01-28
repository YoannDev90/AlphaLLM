import logging

import discord

from bots.bot import bot as main_bot
from config import LOGGER_NAME
from utils.database.server_conf import add_to_allowed_channels, add_to_allowed_roles

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(
        name="whitelist_all",
        description="Whitelist tous les salons et rôles de tous les serveurs",
    )
    async def whitelist_all(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(
            f"Commande /whitelist_all exécutée par {interaction.user.display_name}"
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
                logger.error(
                    f"Erreur lors de la mise à jour du serveur {guild.name}: {e}"
                )

        await interaction.followup.send(
            f"Whitelist mis à jour pour {updated_guilds}/{total_guilds} serveurs.",
            ephemeral=True,
        )
