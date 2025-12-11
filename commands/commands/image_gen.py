import asyncio
from io import BytesIO

import discord
from discord import app_commands

from utils.image_gen import ImageGeneration, ImageGenerationFormat
from utils.ai_process.ai_utils import enhance_image_prompt
from utils.config import LOGGER_NAME
from utils.core.logger import get_logger
from utils.database.models.blacklist import BlacklistManager
from utils.database.models.user_manager import UserManager
from embeds.image import ImageView

logger = get_logger(LOGGER_NAME)

blacklist_manager = BlacklistManager()
user_manager = UserManager()

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
        app_commands.Choice(name="Flux Schnell", value="flux"),
        app_commands.Choice(name="Flux Kontext", value="kontext"),
        app_commands.Choice(name="Seedream", value="seedream"),
        app_commands.Choice(name="NanoBanana", value="nanobanana"),
        app_commands.Choice(name="DALL-E 3", value="dalle"),
        app_commands.Choice(name="GPT Image", value="gptimage"),
        app_commands.Choice(name="Imagen 4", value="imagen"),
        app_commands.Choice(name="Qwen Image", value="qwenimage"),
        app_commands.Choice(name="Grok Image", value="grokimage"),
        app_commands.Choice(name="SDXL", value="sdxl"),
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

        entries = []
        try:
            entries = await asyncio.to_thread(blacklist_manager.fetch_all)
        except Exception as exc:
            logger.debug(f"Failed to fetch blacklist entries: {exc}")

        def _matches_blacklist(entry: dict) -> bool:
            try:
                return int(entry.get("id_discord", 0)) == interaction.user.id
            except Exception:
                return False

        blacklist_entry = next((entry for entry in entries if _matches_blacklist(entry)), None)
        if blacklist_entry:
            reason = blacklist_entry.get("reason", "Unspecified")
            logger.info(
                f"Génération d'image de {interaction.user.display_name} (ID: {interaction.user.id}) ignorée - Liste noire - Motif: {reason}",
            )
            await interaction.followup.send(
                f"⛔️ You are blacklisted from the bot (<@{interaction.user.id}>) - Reason: **{reason}**",
            )
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
        nsfw_detected = False
        
        for i, current_prompt in enumerate(prompts_to_generate, 1):
            try:
                logger.info(f"Generating image {i}/{number} with prompt: {current_prompt}")
                gen = ImageGeneration(current_prompt, model, size, ImageGenerationFormat.BYTES)
                image_data = await gen.generate()
                
                nsfw = False
                images_data.append((image_data, nsfw, current_prompt, i))
                logger.info(f"Image {i}/{number} générée pour {interaction.user.display_name}")
            except Exception as e:
                logger.error(f"Erreur génération image {i}: {str(e)}")
                images_data.append((None, False, current_prompt, i))

        if nsfw_detected and not interaction.channel.is_nsfw():
            logger.warning(f"Image NSFW générée par {interaction.user.display_name} dans un canal non NSFW")
            await interaction.followup.send("🔞 One or more images are NSFW and cannot be sent in a non-NSFW channel.")
            return
        
        success_count = 0
        failed_count = 0
        
        logger.debug(f"Début de l'envoi de {len(images_data)} image(s) pour {interaction.user.display_name}")
        
        if warning_message:
            await interaction.followup.send(warning_message.rstrip())
        
        for image_data, nsfw, current_prompt, image_num in images_data:
            logger.debug(f"Traitement de l'image {image_num}/{number} - Données présentes: {image_data is not None}")
            if image_data:
                try:
                    file = discord.File(BytesIO(image_data), filename=f"generated_image_{image_num}.png")
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