import logging
import random
import string
from datetime import datetime

import discord
from discord import app_commands

from config import LOGGER_NAME
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
        enhance="Whether to enhance the image (default: Yes)",
        style="Artistic style to apply (optional)",
    )
    @app_commands.choices(
        model=[
            app_commands.Choice(name="Flux", value="flux"),
            app_commands.Choice(name="Nano banana", value="nanobanana"),
            app_commands.Choice(name="GPT Image", value="gptimage"),
            app_commands.Choice(name="Z image", value="zimage"),
        ]
    )
    @app_commands.choices(
        size=[
            app_commands.Choice(name="Square (1024x1024)", value="1024x1024"),
            app_commands.Choice(name="Landscape (2048x1024)", value="2048x1024"),
            app_commands.Choice(name="Portrait (1024x2048)", value="1024x2048"),
            app_commands.Choice(name="Small square (768x768)", value="768x768"),
            app_commands.Choice(name="Small landscape (1536x768)", value="1536x768"),
            app_commands.Choice(name="Small portrait (768x1536)", value="768x1536"),
            app_commands.Choice(name="Large square (2048x2048)", value="2048x2048"),
        ]
    )
    @app_commands.choices(
        style=[
            app_commands.Choice(name="3D Render", value="3d_render"),
            app_commands.Choice(name="Abstract", value="abstract"),
            app_commands.Choice(name="Animated", value="animated"),
            app_commands.Choice(name="Art Deco", value="art_deco"),
            app_commands.Choice(name="Comic Book", value="comic_book"),
            app_commands.Choice(name="Concept Art", value="concept_art"),
            app_commands.Choice(name="Drawing", value="drawing"),
            app_commands.Choice(name="Fantasy", value="fantasy"),
            app_commands.Choice(name="Film Noir", value="film_noir"),
            app_commands.Choice(name="Gothic", value="gothic"),
            app_commands.Choice(name="Graffiti", value="graffiti"),
            app_commands.Choice(name="Illustration", value="illustration"),
            app_commands.Choice(name="Kawaii", value="kawaii"),
            app_commands.Choice(name="Landscape", value="landscape"),
            app_commands.Choice(name="Logo", value="logo"),
            app_commands.Choice(name="Minimalist", value="minimalist"),
            app_commands.Choice(name="Oil Painting", value="oil_painting"),
            app_commands.Choice(name="Pixel Art", value="pixel_art"),
            app_commands.Choice(name="Pop Art", value="pop_art"),
            app_commands.Choice(name="Portrait", value="portrait"),
            app_commands.Choice(name="Sci-Fi", value="sci_fi"),
            app_commands.Choice(name="Steampunk", value="steampunk"),
            app_commands.Choice(name="Surreal", value="surreal"),
            app_commands.Choice(name="Vintage Retro", value="vintage_retro"),
            app_commands.Choice(name="Watercolor", value="watercolor"),
        ]
    )
    @app_commands.choices(
        enhance=[
            app_commands.Choice(name="Yes", value="true"),
            app_commands.Choice(name="No", value="false"),
        ]
    )
    async def image_gen(
        interaction: discord.Interaction,
        prompt: str,
        model: str = "Flux",
        size: str = "1024x1024",
        style: str = None,
        number: int = 1,
        enhance: str = "true",
    ):
        await interaction.response.defer()
        perms_checker = PermissionChecker()
        authorized, reason = await perms_checker.is_authorized_int(interaction)
        if not authorized:
            await interaction.followup.send(f"⛔️ {reason}")
            return

        logger.info(
            f"Command /image-gen executed by {interaction.user.display_name} ({interaction.user.id})"
        )
        logger.info(f"prompt: {prompt}, model: {model}, size: {size}, style: {style}, number: {number}")

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
        model = "Flux" if not model else model
        size = "1024x1024" if not size else size
        enhance_bool = enhance.lower() == "true"

        try:
            logger.debug(f"Generating images with prompt: {prompt}")
            results = await unified_image_gen(
                prompt,
                model,
                number,
                size=size,
                style=style,
                enhance=enhance_bool,
                format=Format.BYTES,
                user_id=interaction.user.id,
            )
            if results:
                logger.info(f"Images generated for {interaction.user.display_name}")
            else:
                logger.error("Failed to generate images")
        except Exception as e:
            logger.error(f"Error generating images: {str(e)}")

        logger.debug(
            f"Start sending {len(results)} image(s) for {interaction.user.display_name}"
        )

        if warning_message:
            await interaction.followup.send(warning_message.rstrip())

        for idx, (image_data, current_prompt) in enumerate(results, start=1):
            logger.debug(
                f"Image processing {idx}/{number} -Data present: {image_data is not None}"
            )
            if image_data:
                try:
                    filename = f"{datetime.now().strftime('%m%d%H%M%S%f')}_{''.join(random.choices(string.ascii_letters + string.digits, k=10))}.png"
                    file = discord.File(image_data, filename=filename)
                    # view = ImageView(current_prompt, model, size, enhance)

                    logger.debug(f"Attempting to send the image {idx}/{number}")

                    if not warning_message:
                        await interaction.followup.send(
                            # f"🎨 Image {idx}/{number}:\n```{current_prompt}```",
                            file=file,
                            # view=view
                        )
                    else:
                        await interaction.followup.send(
                            # f"🎨 Image {idx}/{number}:\n```{current_prompt}```",
                            file=file,
                            # view=view
                        )

                    # view.message = message
                except Exception as e:
                    logger.error(f"Error sending image {idx}/{number}: {str(e)}")
            else:
                logger.error(
                    f"Failed to generate image {idx}/{number} For {interaction.user.display_name}"
                )
