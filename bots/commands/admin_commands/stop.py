import datetime
import json
import logging
from pathlib import Path

import discord

from config import DEV_IDS, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(name="stop", description="Stop the bot")
    async def stop(interaction: discord.Interaction):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message(
                "❌ You are not authorized to use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Command /stop executed by {interaction.user.display_name}")

        await interaction.followup.send("🛑 Complete bot shutdown...", ephemeral=True)
        logger.info("Stop request received")

        with open(Path("stop.json"), "w") as f:
            json.dump(
                {"COMMAND": "STOP", "timestamp": datetime.datetime.now().isoformat()}, f
            )

        logger.info("stop.json file created, main process will stop the bot.")
