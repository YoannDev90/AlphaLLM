import datetime
import json
import logging
from pathlib import Path

import discord

from config import DEV_IDS, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(name="restart", description="Restart the bot")
    async def restart(interaction: discord.Interaction):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message(
                "❌ You are not authorized to use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Command /restart executed by {interaction.user.display_name}")

        await interaction.followup.send("🛑 Complete bot restart...", ephemeral=True)
        logger.info("Demande de redémarrage reçue")

        with open(Path("stop.json"), "w") as f:
            json.dump(
                {
                    "COMMAND": "RESTART",
                    "timestamp": datetime.datetime.now().isoformat(),
                },
                f,
            )

        logger.info(
            "Fichier stop.json créé, le processus principal va redémarrer le bot."
        )
