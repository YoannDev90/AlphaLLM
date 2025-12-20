import datetime
import json
import logging

import discord

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def setup(bot: discord.Client):
    @bot.tree.command(name="stop", description="Arrête le bot")
    async def stop(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /stop exécutée par {interaction.user.display_name}")

        await interaction.followup.send("🛑 Arrêt complet du bot...", ephemeral=True)
        logger.info("Demande d'arrêt reçue")

        with open("stop.json", "w") as f:
            json.dump({"COMMAND": "STOP", "timestamp": datetime.datetime.now().isoformat()}, f)
        
        logger.info("Fichier stop.json créé, le processus principal va arrêter le bot.")
