import discord
import logging
from utils.config import logger_name, GUILD_ID, is_dev_id, LOGGER_NAME
import sys
import os
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(logger_name)

async def setup(bot: discord.Client):
    @bot.tree.command(name="restart", description="Redémarre le bot")
    async def restart(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /restart exécutée par {interaction.user.display_name}")

        if not is_dev_id(interaction.user.id):
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        await interaction.followup.send("🛑 Redémarrage complet du bot...", ephemeral=True)
        logger.info("Demande de redémarrage reçue")

        if bot.is_closed():
            return

        await bot.close()
        sys.exit(0)
