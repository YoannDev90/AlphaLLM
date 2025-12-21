import logging

import discord
from discord import app_commands

from config import LOGGER_NAME
from utils.handlers.messages import smart_long_messages

logger = logging.getLogger(LOGGER_NAME)

async def setup(bot: discord.Client):
    @bot.tree.command(name="test", description="Send a test markdown message")
    async def test(interaction: discord.Interaction):
        logger.info(f"Commande /test exécutée par {interaction.user.display_name}")
        await interaction.response.defer()
        try:
            with open('test.md', 'r') as f:
                response = f.read()
            await smart_long_messages(interaction.channel, response)
            await interaction.followup.send("Test message sent.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in test command: {e}")
            await interaction.followup.send("An error occurred while sending the test message.", ephemeral=True)