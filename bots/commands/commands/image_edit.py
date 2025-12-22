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
from utils.handlers.images import upload_images
from utils.unified_image import Format, unified_image_edit, unified_image_transform

logger = logging.getLogger(LOGGER_NAME)

async def setup(bot: discord.Client):
    @bot.tree.command(name="image-edit", description="Edit an image with AI models or apply transformations")
    @app_commands.describe(
        prompt="The prompt to edit the image (optional if using transformations)",
        model="The model to use for editing (default: kontext)",
        number="Number of images to generate (1-4, default: 1)",
        enhance="Whether to enhance the prompt (default: Yes)",
        remove_bg="Remove background",
        enhance_img="Enhance image quality",
        upscale="Upscale image resolution",
        restore="Restore image (remove artifacts)",
        improve="Improve image colors and lighting",
        auto_enhance="Auto enhance image",
        images="Attach the image to edit"
    )
    @app_commands.choices(model=[
        app_commands.Choice(name="Flux Kontext", value="kontext"),
        app_commands.Choice(name="Seedream 4", value="seedream"),
        app_commands.Choice(name="NanoBanana", value="nanobanana"),
        app_commands.Choice(name="GPT Image 1", value="gptimage"),
    ])
    async def image_edit(
        interaction: discord.Interaction,
        images: discord.Attachment,
        prompt: str = None,
        model: str = "kontext",
        number: int = 1,
        enhance: bool = True,
        remove_bg: bool = False,
        enhance_img: bool = False,
        upscale: bool = False,
        restore: bool = False,
        improve: bool = False,
        auto_enhance: bool = False,
    ):
        await interaction.response.defer()
        perms_checker = PermissionChecker()
        authorized, reason = await perms_checker.is_authorized_int(interaction)
        if not authorized:
            await interaction.followup.send(f"⛔️ {reason}")
            return
        
        logger.info(f"Commande /image-edit exécutée par {interaction.user.display_name} ({interaction.user.id})")
        logger.info(f"Prompt: {prompt}, model: {model}, number: {number}")

        original_number = number
        warning_message = ""
        
        if number < 1:
            number = 1
            warning_message = "⚠️ Number adjusted from less than 1 to 1.\n"
        elif number > 4:
            number = 4
            warning_message = f"⚠️ Number adjusted from {original_number} to 4 (maximum allowed).\n"
        model = "kontext" if not model else model

        trans_list = []
        if remove_bg:
            trans_list.append('remove_bg')
        if enhance_img:
            trans_list.append('enhance')
        if upscale:
            trans_list.append('upscale')
        if restore:
            trans_list.append('generative_restore')
        if improve:
            trans_list.append('improve')
        if auto_enhance:
            trans_list.append('auto_enhance')

        if not prompt and not trans_list:
            await interaction.followup.send("❌ Please provide a prompt or select at least one transformation.")
            return

        edit = bool(prompt)
        images_url = [images.url]

        try:
            logger.debug(f"Processing image with prompt: {prompt or 'None'}")
            if edit:
                results = await unified_image_edit(prompt, model, number, enhance=enhance and bool(prompt), format=Format.BYTES, images_url=images_url, user_id=interaction.user.id)
                if trans_list:
                    new_results = []
                    for image_data, current_prompt in results:
                        if image_data:
                            image_bytes = image_data.getvalue()
                            uploaded_urls = await upload_images([image_bytes])
                            if uploaded_urls:
                                transformed_result = await unified_image_transform(trans_list, format=Format.BYTES, image_url=uploaded_urls[0], user_id=interaction.user.id)
                                new_results.append((transformed_result, current_prompt))
                            else:
                                new_results.append((None, current_prompt))
                        else:
                            new_results.append((None, current_prompt))
                    results = new_results
            elif trans_list:
                transformed_result = await unified_image_transform(trans_list, format=Format.BYTES, image_url=images_url[0], user_id=interaction.user.id)
                results = [(transformed_result, "")] * number
            else:
                results = []
            if results:
                logger.info(f"Images processed for {interaction.user.display_name}")
            else:
                logger.error(f"Failed to process images")
        except Exception as e:
            logger.error(f"Error editing images: {str(e)}")
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")
            return
        
        logger.debug(f"Début de l'envoi de {len(results)} image(s) pour {interaction.user.display_name}")
        
        if warning_message:
            await interaction.followup.send(warning_message.rstrip())
        
        for idx, (image_data, current_prompt) in enumerate(results, start=1):
            logger.debug(f"Traitement de l'image {idx}/{number} - Données présentes: {image_data is not None}")
            if image_data:
                try:
                    filename = f"{datetime.now().strftime('%m-%d_%H%-M-%S-%f')}_{''.join(random.choices(string.ascii_letters + string.digits, k=10))}.png"
                    file = discord.File(image_data, filename=filename)
                    
                    logger.debug(f"Tentative d'envoi de l'image {idx}/{number}")
                    
                    message = await interaction.followup.send(file=file)
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi de l'image {idx}/{number}: {str(e)}")
                    await interaction.followup.send(f"❌ Error sending image {idx}: {str(e)}")
            else:
                logger.error(f"Échec de l'image {idx}/{number} pour {interaction.user.display_name}")
                await interaction.followup.send(f"❌ Failed to process image {idx}.")