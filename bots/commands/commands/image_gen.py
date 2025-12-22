import asyncio
import logging
import random
import string
from datetime import datetime
from io import BytesIO

import discord
from discord import app_commands

from config import LOGGER_NAME
from utils.ai_process.ai_utils import enhance_image_prompt
from utils.discord_utils.permission_checker import PermissionChecker
from utils.unified_image import Format, unified_image_gen

logger = logging.getLogger(LOGGER_NAME)

async def setup(bot: discord.Client):
    @bot.tree.command(name="image-gen", description="Generate an image from a prompt")
    @app_commands.describe(
        prompt="The prompt to generate the image from",
        model="The model to use for image generation (default: flux)",
        size="The size of the image (default: 1024x1024)",
        number="Number of images to generate (1-4, default: 2)",
        enhance="Whether to enhance the image (default: Yes)"
    )
    @app_commands.choices(model=[
        app_commands.Choice(name="Flux 2", value="flux"),
        app_commands.Choice(name="Flux Kontext", value="kontext"),
        app_commands.Choice(name="Seedream 4", value="seedream"),
        app_commands.Choice(name="NanoBanana", value="nanobanana"),
        app_commands.Choice(name="GPT Image 1", value="gptimage"),
        app_commands.Choice(name="Z-Image", value="zimage"),
    ])
    @app_commands.choices(size=[
        app_commands.Choice(name="Square (1024x1024)", value="1024x1024"),
        app_commands.Choice(name="Landscape (2048x1024)", value="2048x1024"),
        app_commands.Choice(name="Portrait (1024x2048)", value="1024x2048"),
        app_commands.Choice(name="Small square (768x768)", value="768x768"),
        app_commands.Choice(name="Small landscape (1536x768)", value="1536x768"),
        app_commands.Choice(name="Small portrait (768x1536)", value="768x1536"),
        app_commands.Choice(name="Large square (2048x2048)", value="2048x2048")
    ])
    async def image_gen(
        interaction: discord.Interaction,
        prompt: str,
        model: str = "flux",
        size: str = "1024x1024",
        number: int = 1,
        enhance: bool = True,
    ):
        await interaction.response.defer()
        perms_checker = PermissionChecker()
        authorized, reason = await perms_checker.is_authorized_int(interaction)
        if not authorized:
            await interaction.followup.send(f"⛔️ {reason}")
            return
        
        logger.info(f"Commande /image-gen exécutée par {interaction.user.display_name} ({interaction.user.id})")
        logger.info(f"Prompt: {prompt}, model: {model}, size: {size}, number: {number}")

        original_number = number
        warning_message = ""
        
        if number < 1:
            number = 1
            warning_message = "⚠️ Number adjusted from less than 1 to 1.\n"
        elif number > 4:
            number = 4
            warning_message = f"⚠️ Number adjusted from {original_number} to 4 (maximum allowed).\n"
        model = "flux" if not model else model
        size = "1024x1024" if not size else size
        
        try:
            logger.debug(f"Generating images with prompt: {prompt}")
            results = await unified_image_gen(prompt, model, number, size=size, enhance=enhance, format=Format.BYTES, user_id=interaction.user.id)
            if results:
                logger.info(f"Images generated for {interaction.user.display_name}")
            else:
                logger.error(f"Failed to generate images")
        except Exception as e:
            logger.error(f"Error generating images: {str(e)}")
        
        logger.debug(f"Début de l'envoi de {len(results)} image(s) pour {interaction.user.display_name}")
        
        if warning_message:
            await interaction.followup.send(warning_message.rstrip())
        
        for idx, (image_data, current_prompt) in enumerate(results, start=1):
            logger.debug(f"Traitement de l'image {idx}/{number} - Données présentes: {image_data is not None}")
            if image_data:
                try:
                    filename = f"{datetime.now().strftime('%m-%d_%H%-M-%S-%f')}_{''.join(random.choices(string.ascii_letters + string.digits, k=10))}.png"
                    file = discord.File(image_data, filename=filename)
                    #view = ImageView(current_prompt, model, size, enhance)
                    
                    logger.debug(f"Tentative d'envoi de l'image {idx}/{number}")
                    
                    if not warning_message:
                        message = await interaction.followup.send(
                            #f"🎨 Image {idx}/{number}:\n```{current_prompt}```", 
                            file=file, 
                            #view=view
                        )
                    else:
                        message = await interaction.followup.send(
                            #f"🎨 Image {idx}/{number}:\n```{current_prompt}```", 
                            file=file, 
                            #view=view
                        )
                    
                    #view.message = message
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi de l'image {idx}/{number}: {str(e)}")
            else:
                logger.error(f"Échec de l'image {idx}/{number} pour {interaction.user.display_name}")