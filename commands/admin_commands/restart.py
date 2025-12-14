import datetime
import json
import logging

import discord

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def setup(bot: discord.Client):
    @bot.tree.command(name="restart", description="Redémarre le bot")
    async def restart(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /restart exécutée par {interaction.user.display_name}")

        await interaction.followup.send("🛑 Redémarrage complet du bot...", ephemeral=True)
        logger.info("Demande de redémarrage reçue")

        with open("stop.json", "w") as f:
            json.dump({"COMMAND": "RESTART", "timestamp": datetime.datetime.now().isoformat()}, f)
        
        logger.info("Fichier stop.json créé, le processus principal va redémarrer le bot.")
