import logging

import discord

from bots.bot import bot as main_bot
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(name="leave", description="Fait quitter le bot d'un serveur")
    async def leave(interaction: discord.Interaction, guild_id: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(
            f"Commande /leave exécutée par {interaction.user.display_name} pour le serveur {guild_id}"
        )

        if not guild_id.isdigit() or int(guild_id) <= 0:
            await interaction.followup.send(
                "L'ID du serveur fourni est invalide.", ephemeral=True
            )
            return

        guild = main_bot.get_guild(int(guild_id))
        if guild is None:
            await interaction.followup.send(
                "Le bot n'est pas présent dans ce serveur ou l'ID est incorrect.",
                ephemeral=True,
            )
            return

        try:
            await guild.leave()
            await interaction.followup.send(
                f"Le bot a quitté le serveur **{guild.name}** (ID: `{guild_id}`).",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            logger.error(
                f"Erreur HTTP lors de la tentative de quitter le serveur {guild_id}: {e}"
            )
            await interaction.followup.send(
                "Erreur lors de la tentative de quitter le serveur. Veuillez réessayer plus tard.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(
                f"Erreur inattendue lors de la tentative de quitter le serveur {guild_id}: {e}"
            )
            await interaction.followup.send(
                "Erreur inattendue. Veuillez réessayer plus tard.", ephemeral=True
            )
