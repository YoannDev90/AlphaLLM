import asyncio
import logging
import random
import string
from datetime import datetime
from io import BytesIO

import discord
from discord import app_commands

from config import LOGGER_NAME
from utils.discord_utils.permission_checker import PermissionChecker
from utils.unified_image import Format, unified_image_edit

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(
        name="image-edit",
        description="Edit an image with AI models or apply transformations",
    )
    @app_commands.describe(
        prompt="The prompt to edit the image (optional if using transformations)",
        model="The model to use for editing (default: kontext)",
        number="Number of images to generate (1-4, default: 1)",
        enhance="Whether to enhance the image (default: Yes)",
        image_1="Attach the first image to edit",
        image_2="Attach the second image to edit (optional)",
        image_3="Attach the third image to edit (optional)",
        image_4="Attach the fourth image to edit (optional)",
    )
    @app_commands.choices(
        model=[
            app_commands.Choice(name="Flux Kontext", value="kontext"),
            app_commands.Choice(name="Seedream 4", value="seedream"),
            app_commands.Choice(name="NanoBanana", value="nanobanana"),
            app_commands.Choice(name="GPT Image 1", value="gptimage"),
        ]
    )
    async def image_edit(
        interaction: discord.Interaction,
        prompt: str,
        image_1: discord.Attachment,
        image_2: discord.Attachment = None,
        image_3: discord.Attachment = None,
        image_4: discord.Attachment = None,
        model: str = None,
        number: int = 1,
        enhance: bool = True,
    ):
        await interaction.response.defer()
        perms_checker = PermissionChecker()
        authorized, reason = await perms_checker.is_authorized_int(interaction)
        if not authorized:
            await interaction.followup.send(f"⛔️ {reason}")
            return

        logger.info(
            f"Commande /image-edit exécutée par {interaction.user.display_name} ({interaction.user.id})"
        )
        logger.info(f"Prompt: {prompt}, model: {model}, number: {number}")

        original_number = number
        warning_message = ""

        if number < 1:
            number = 1
            warning_message = "⚠️ Number adjusted from less than 1 to 1.\n"
        elif number > 4:
            number = 4
            warning_message = (
                f"⚠️ Number adjusted from {original_number} to 4 (maximum allowed).\n"
            )
        model = "kontext" if not model else model

        images_url = [image_1.url]
        if image_2:
            images_url.append(image_2.url)
        if image_3:
            images_url.append(image_3.url)
        if image_4:
            images_url.append(image_4.url)

        try:
            logger.debug(f"Processing image with prompt: {prompt}")
            results = await unified_image_edit(
                prompt,
                model,
                number,
                enhance=enhance,
                format=Format.BYTES,
                images_url=images_url,
                user_id=interaction.user.id,
            )
        except Exception as e:
            logger.error(f"Error editing images: {str(e)}")
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")
            return

        logger.info(
            f"Début de l'envoi de {len(results)} image(s) pour {interaction.user.display_name}"
        )

        if warning_message:
            await interaction.followup.send(warning_message.rstrip())

        for idx, (image_data, current_prompt) in enumerate(results, start=1):
            logger.info(
                f"Traitement de l'image {idx}/{number} - Données présentes: {image_data is not None}"
            )
            if image_data:
                try:
                    filename = f"{datetime.now().strftime('%m-%d_%H%-M-%S-%f')}_{''.join(random.choices(string.ascii_letters + string.digits, k=10))}.png"
                    file = discord.File(image_data, filename=filename)

                    logger.debug(f"Tentative d'envoi de l'image {idx}/{number}")

                    message = await interaction.followup.send(file=file)

                except Exception as e:
                    logger.error(
                        f"Erreur lors de l'envoi de l'image {idx}/{number}: {str(e)}"
                    )
                    await interaction.followup.send(
                        f"❌ Error sending image {idx}: {str(e)}"
                    )
            else:
                logger.error(
                    f"Échec de l'image {idx}/{number} pour {interaction.user.display_name}"
                )
                await interaction.followup.send(f"❌ Failed to process image {idx}.")
