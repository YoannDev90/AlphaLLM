import asyncio
from io import BytesIO

import discord
import logging
from discord import app_commands

from utils.unified_image import unified_image_manager, Format
from utils.ai_process.ai_utils import enhance_image_prompt
from utils.discord_utils.permission_checker import PermissionChecker

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

async def setup(bot: discord.Client):
    @bot.tree.command(name="image", description="Generate an image from a prompt")
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
        app_commands.Choice(name="DALL-E 3", value="dalle"),
        app_commands.Choice(name="GPT Image 1", value="gptimage"),
        app_commands.Choice(name="Imagen 4", value="imagen"),
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
    async def image(
        interaction: discord.Interaction,
        prompt: str,
        model: str = "flux",
        size: str = "1024x1024",
        number: int = 1,
        enhance: bool = True,
    ):
        await interaction.response.defer()
        checker = PermissionChecker()
        authorized, reason = checker.is_authorized(interaction)
        if not authorized:
            await interaction.followup.send(f"⛔️ {reason}")
            return
        
        logger.info(f"Commande /image exécutée par {interaction.user.display_name} ({interaction.user.id})")
        logger.info(f"Prompt: {prompt}, model: {model}, size: {size}, number: {number}")

        original_number = number
        warning_message = ""
        
        if number < 1:
            number = 1
            warning_message = "⚠️ Number adjusted from less than 1 to 1.\n"
        elif number > 3:
            number = 3
            warning_message = f"⚠️ Number adjusted from {original_number} to 3 (maximum allowed).\n"

        for _ in range(number):
            await asyncio.to_thread(user_manager.record_image_usage, interaction.user.id)
        try:
            await asyncio.to_thread(user_manager.record_interaction, interaction.user.id)
        except Exception as exc:
            logger.debug(f"Failed to record interaction: {exc}")
        model = "flux" if not model else model
        size = "1024x1024" if not size else size
        
        if enhance:
            enhanced_prompts = await enhance_image_prompt(prompt, number)
            prompts_to_generate = []
            for i in range(1, number + 1):
                if i in enhanced_prompts:
                    prompts_to_generate.append(enhanced_prompts[i])
                else:
                    prompts_to_generate.append(prompt)
        else:
            prompts_to_generate = [prompt] * number

        images_data = []
        
        for current_prompt in prompts_to_generate:
            try:
                logger.info(f"Generating image with prompt: {current_prompt}")
                result = await unified_image_manager(current_prompt, model, num_images=1, size=size, enhance=False, format=Format.BYTES, user_id=interaction.user.id)
                image_data = result[0] if result else None
                images_data.append((image_data, current_prompt))
                if image_data:
                    logger.info(f"Image generated for {interaction.user.display_name}")
                else:
                    logger.error(f"Failed to generate image")
            except Exception as e:
                logger.error(f"Error generating image: {str(e)}")
                images_data.append((None, current_prompt))

        success_count = 0
        failed_count = 0
        
        logger.debug(f"Début de l'envoi de {len(images_data)} image(s) pour {interaction.user.display_name}")
        
        if warning_message:
            await interaction.followup.send(warning_message.rstrip())
        
        for idx, (image_data, current_prompt) in enumerate(images_data, 1):
            image_num = idx
            logger.debug(f"Traitement de l'image {image_num}/{number} - Données présentes: {image_data is not None}")
            if image_data:
                try:
                    file = discord.File(image_data, filename=f"generated_image_{image_num}.png")
                    view = ImageView(current_prompt, model, size, enhance)
                    
                    logger.debug(f"Tentative d'envoi de l'image {image_num}/{number}")
                    
                    if success_count == 0 and not warning_message:
                        message = await interaction.followup.send(
                            f"🎨 Image {image_num}/{number}:\n```{current_prompt}```", 
                            file=file, 
                            view=view
                        )
                    else:
                        message = await interaction.followup.send(
                            f"🎨 Image {image_num}/{number}:\n```{current_prompt}```", 
                            file=file, 
                            view=view
                        )
                    
                    view.message = message
                    success_count += 1
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi de l'image {image_num}/{number}: {str(e)}")
                    failed_count += 1
            else:
                failed_count += 1
                logger.error(f"Échec de l'image {image_num}/{number} pour {interaction.user.display_name}")
        
        if failed_count > 0:
            await interaction.followup.send(f"❌ {failed_count}/{number} image(s) failed to generate.")
        
        logger.info(f"{success_count}/{number} image(s) générée(s) et envoyée(s) à {interaction.user.display_name}")