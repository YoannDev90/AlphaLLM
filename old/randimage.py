"""
randimage.py

This module defines the `/randimage` command, which generates a random image using a prompt.
"""

import discord
from discord import app_commands
from utils.image_gen import generate_image
from models.cerebras import cerebras
from utils.langs import get_translation
from utils.gallery import gallery
from io import BytesIO
import logging
import random
import os

logger = logging.getLogger('AlphaLLM')

PUBLIC_IMAGE_CHANNEL_ID = os.getenv("GALERIE_ID")

async def setup(bot: discord.Client):
    """
    Sets up the `/randimage` command for the bot.

    Args:
        bot (discord.Client): The Discord bot instance.
    """
    @bot.tree.command(name="randimage", description="Génère une image aléatoire")
    async def randimage(interaction: discord.Interaction):
        """
        Generates a random image using a prompt and sends it to the user.

        Args:
            interaction (discord.Interaction): The interaction object for the command.
        """
        logger.info(f"Commande randimage exécutée par {interaction.user.display_name}")

        await interaction.response.defer()

        try:
            prompt = await cerebras("Generate a random prompt image, only keywords, no sentences", "llamalight")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du prompt pour {interaction.user.display_name}")

        model = "flux"
        width = 1024
        height = 1024
        nologo = True
        private = False
        enhance = True
        safe = True
        seed = None
        image_data = await generate_image(prompt, model, seed, width, height, nologo, private, enhance, safe)
    
        if image_data:
            file = discord.File(BytesIO(image_data), filename="generated_image.png")
            await interaction.followup.send(file=file)
            logger.info(f"Image générée et envoyée à {interaction.user.display_name}")
            if not private and safe:
                await gallery(bot, image_data, prompt, interaction)
        else:
            await interaction.followup.send("Impossible de générer l'image.")
            logger.error(f"Échec de la génération d'image pour {interaction.user.display_name}")