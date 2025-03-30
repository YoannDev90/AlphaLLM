"""
multimage.py

This module defines the `/multimage` command, which generates multiple images
based on a given prompt and user-defined parameters.
"""

import discord
from discord import app_commands
from utils.image_gen import generate_image
from models.cerebras import cerebras
from io import BytesIO
from utils.langs import get_translation
from utils.gallery import gallery
import logging
import random
import os

logger = logging.getLogger('AlphaLLM')

PUBLIC_IMAGE_CHANNEL_ID = os.getenv("GALERIE_ID")

async def setup(bot: discord.Client):
    """
    Sets up the `/multimage` command for the bot.

    Args:
        bot (discord.Client): The Discord bot instance.
    """
    @bot.tree.command(name="multimage", description="Génère plusieurs images à partir d'un prompt")
    @app_commands.choices(model=[
        app_commands.Choice(name="Flux", value="flux"),
        app_commands.Choice(name="Turbo", value="turbo")
    ])
    async def multimage(
        interaction: discord.Interaction,
        prompt: str,
        number: int = 2,
        model: str = "flux",
        width: int = 1024,
        height: int = 1024,
        nologo: bool = True,
        private: bool = False,
        enhance: bool = False,
        safe: bool = True
    ):
        """
        Generates multiple images based on the given prompt and parameters.

        Args:
            interaction (discord.Interaction): The interaction object for the command.
            prompt (str): The prompt for image generation.
            number (int, optional): The number of images to generate. Defaults to 2.
            model (str, optional): The model to use for generation. Defaults to "flux".
            width (int, optional): The width of the images. Defaults to 1024.
            height (int, optional): The height of the images. Defaults to 1024.
            nologo (bool, optional): Whether to exclude logos. Defaults to True.
            private (bool, optional): Whether the images are private. Defaults to False.
            enhance (bool, optional): Whether to enhance the images. Defaults to False.
            safe (bool, optional): Whether to enable safe mode. Defaults to True.
        """
        logger.info(f"Commande multimage exécutée par {interaction.user.display_name}")
        
        if width > 2048 or height > 2048:
            await interaction.response.send_message("Les dimensions de l'image doivent être inférieures ou égales à 2048x2048.")
            logger.error(f"Dimensions de l'image trop grandes pour {interaction.user.display_name}")
            width = 2048
            height = 2048
        
        if number > 4:
            await interaction.response.send_message("Le nombre d'images générées doit être inférieur ou égal à 4.")
            logger.error(f"Nombre d'images trop grand pour {interaction.user.display_name}")
            number = 4

        await interaction.response.send_message("Génération des images en cours...")
        interaction_channel = interaction.channel

        safe = True if interaction.guild and interaction.guild.nsfw_level == discord.NSFWLevel.default and not interaction.channel.is_nsfw() else safe

        for i in range(number):
            seed = random.randint(0, 1000000)
            image_data = await generate_image(prompt, model, seed, width, height, nologo, private, enhance, safe)
            
            if image_data:
                file = discord.File(BytesIO(image_data), filename=f"generated_image_{i+1}.png")
                await interaction_channel.send(file=file)
                logger.info(f"Image {i+1}/{number} générée et envoyée à {interaction.user.display_name}")
                if not private and safe:
                    await gallery(bot, image_data, prompt, interaction)
            else:
                await interaction.followup.send(f"Impossible de générer l'image {i+1}.")
                logger.error(f"Échec de la génération de l'image {i+1} pour {interaction.user.display_name}")