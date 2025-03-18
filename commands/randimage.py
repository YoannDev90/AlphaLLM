import discord
from discord import app_commands
from models.polli_image_models import generate_image
from models.cerebras import cerebras
from utils.langs import get_translation
from io import BytesIO
import logging
import random

logger = logging.getLogger('AlphaLLM')

PUBLIC_IMAGE_CHANNEL_ID = 1348356829985374328

async def setup(bot: discord.Client):
    @bot.tree.command(name="randimage", description="Génère une image aléatoire")
    async def randimage(interaction: discord.Interaction):
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
            if not private:
                public_channel = interaction.guild.get_channel(PUBLIC_IMAGE_CHANNEL_ID)
                if public_channel:
                    await public_channel.send(file=file)
        else:
            await interaction.followup.send("Impossible de générer l'image.")
            logger.error(f"Échec de la génération d'image pour {interaction.user.display_name}")