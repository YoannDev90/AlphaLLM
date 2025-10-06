import discord
from discord import app_commands
from utils.ai_utils import enhance_image_prompt
from io import BytesIO
import logging
from utils.config import logger_name
from utils.user_config import get_image_model, get_image_size, get_image_private, get_image_enhance
from utils.user_manager import new_interaction, new_image
from utils.database import get_blacklist
from embeds.image import ImageView, EditImageModal
import random
import base64

# Import des fonctions de génération d'images
from models.image.flux import generate_flux
from models.image.kontext import generate_kontext
from models.image.turbo import generate_turbo
from models.image.seedream import generate_seedream
from models.image.nanobanana import generate_nanobanana
from models.image.dalle import generate_dalle
from models.image.flux_schnell import generate_flux_schnell
from models.image.gpt_image import generate_gpt_image
from models.image.imagen import generate_imagen
from models.image.phoenix import generate_phoenix
from models.image.playground import generate_playground
from models.image.recraft import generate_recraft
from models.image.sana import generate_sana
from models.image.sdlarge import generate_sdlarge
from models.image.sdxl import generate_sdxl

logger = logging.getLogger(logger_name)

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
        app_commands.Choice(name="Flux", value="flux"),
        app_commands.Choice(name="Kontext", value="kontext"),
        app_commands.Choice(name="Turbo", value="turbo"),
        app_commands.Choice(name="Seedream", value="seedream"),
        app_commands.Choice(name="NanoBanana", value="nanobanana"),
        app_commands.Choice(name="DALL-E 3", value="dalle"),
        app_commands.Choice(name="Flux Schnell", value="flux_schnell"),
        app_commands.Choice(name="GPT Image 1", value="gpt_image"),
        app_commands.Choice(name="Imagen 3 Fast", value="imagen"),
        app_commands.Choice(name="Phoenix 1.0", value="phoenix"),
        app_commands.Choice(name="Playground v2.5", value="playground"),
        app_commands.Choice(name="Recraft 20B", value="recraft"),
        app_commands.Choice(name="Sana", value="sana"),
        app_commands.Choice(name="SD 3.5 Large", value="sdlarge"),
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
        number: int = 2,
        enhance: bool = True,
    ):
        await interaction.response.defer()

        blacklist_data = await get_blacklist()
                
        blacklist_entry = next((entry for entry in blacklist_data if entry.get('id_discord') == interaction.user.id), None)
        if blacklist_entry:
            reason = blacklist_entry.get('reason', 'Unspecified')
            logger.info(f"Génération d'image de {interaction.user.display_name} (ID: {interaction.user.id}) ignorée - Liste noire - Motif: {reason}")
            await interaction.followup.send(f"⛔️ You are blacklisted from the bot (<@{interaction.user.id}>) - Reason: **{reason}**")
            return
        
        logger.info(f"Commande /image exécutée par {interaction.user.display_name} ({interaction.user.id})")
        logger.info(f"Prompt: {prompt}, model: {model}, size: {size}, number: {number}")

        original_number = number
        warning_message = ""
        
        if number < 1:
            number = 1
            warning_message = "⚠️ Number adjusted from less than 1 to 1.\n"
        elif number > 4:
            number = 4
            warning_message = f"⚠️ Number adjusted from {original_number} to 4 (maximum allowed).\n"

        new_interaction(interaction.user.id)
        new_image(interaction.user.id)
        model = "flux" if not model else model
        size = "1024x1024" if not size else size
        
        # Mapping des modèles vers leurs fonctions
        model_functions = {
            "flux": generate_flux,
            "kontext": generate_kontext,
            "turbo": generate_turbo,
            "seedream": generate_seedream,
            "nanobanana": generate_nanobanana,
            "dalle": generate_dalle,
            "flux_schnell": generate_flux_schnell,
            "gpt_image": generate_gpt_image,
            "imagen": generate_imagen,
            "phoenix": generate_phoenix,
            "playground": generate_playground,
            "recraft": generate_recraft,
            "sana": generate_sana,
            "sdlarge": generate_sdlarge,
            "sdxl": generate_sdxl,
        }
        
        generate_func = model_functions.get(model, generate_flux)
        
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
                # Appel direct de la fonction de génération qui retourne base64
                image_base64 = await generate_func(current_prompt, size)
                
                # Convertir base64 en bytes
                image_data = base64.b64decode(image_base64)
                
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
                    view = ImageView(current_prompt, model, size, enhance, nsfw)
                    
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