"""
models.py

This module defines the `/models` command, which allows users to configure and
interact with different AI models using interactive buttons.
"""

#commands/models.py

import discord
import logging
from discord import app_commands
from utils.models_buttons import ModelButton
from utils.langs import get_translation
import json

logger = logging.getLogger("AlphaLLM")

with open("config/models.json", "r") as f:
    MODELS = json.load(f)

async def setup(bot: discord.Client):
    """
    Sets up the `/models` command for the bot.

    Args:
        bot (discord.Client): The Discord bot instance.
    """
    @bot.tree.command(name="models", description="Configurer les modèles.")
    async def models(interaction: discord.Interaction):
        """
        Displays a view with buttons to configure and interact with AI models.

        Args:
            interaction (discord.Interaction): The interaction object for the command.
        """
        logger.info(f"Commande models exécutée par {interaction.user.display_name}")
        await interaction.response.defer()
        view = discord.ui.View()
        for model in MODELS:
            view.add_item(ModelButton(bot, model, interaction.guild))
        
        await interaction.followup.send(view=view)
