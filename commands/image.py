import discord
from discord import app_commands
from utils.image_gen import generate_image
from utils.gallery import gallery
from io import BytesIO
import logging
from dotenv import load_dotenv
from utils.langs import get_translation
import random

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="image", description="Génère une image à partir d'un prompt")
    @app_commands.choices(model=[
        app_commands.Choice(name="Flux", value="flux"),
        app_commands.Choice(name="Turbo", value="turbo")
    ])
    async def image(
        interaction: discord.Interaction,
        prompt: str,
        model: str = "flux",
        size: str = "1024x1024",
        private: bool = False,
        enhance: bool = False,
    ):
        logger.info(f"Commande image exécutée par {interaction.user.display_name}")

        width, height = map(int, size.split("x"))
    
        if width > 2048 or height > 2048:
            logger.warning(f"Dimensions de l'image trop grandes pour {interaction.user.display_name}")
            width = 2048
            height = 2048

        await interaction.response.defer()

        seed = None
        nologo = True
        safe = True if interaction.guild and interaction.guild.nsfw_level == discord.NSFWLevel.default and not interaction.channel.is_nsfw() else False
        image_data = await generate_image(prompt, model, seed, width, height, nologo, private, enhance, safe)
    
        if image_data:
            file = discord.File(BytesIO(image_data), filename="generated_image.png")
            view = RegenerateImageView(prompt, model, width, height, nologo, private, enhance, safe)
            await interaction.followup.send(file=file, view=view)
            logger.info(f"Image générée et envoyée à {interaction.user.display_name}")
            if not private and safe:
                await gallery(bot, image_data, prompt, interaction)
        else:
            await interaction.followup.send("Echec de la génération de l'image. Veuillez réessayer.")
            logger.error(f"Échec de la génération d'image pour {interaction.user.display_name}")

class RegenerateImageView(discord.ui.View):
    def __init__(self, prompt, model, width, height, nologo, private, enhance, safe):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.width = width
        self.height = height
        self.nologo = nologo
        self.private = private
        self.enhance = enhance
        self.safe = safe

    @discord.ui.button(label="Régénérer", style=discord.ButtonStyle.primary)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        seed = random.randint(0, 1000000)
        image_data = await generate_image(self.prompt, self.model, seed, self.width, self.height, self.nologo, self.private, self.enhance, self.safe)
        
        if image_data:
            file = discord.File(BytesIO(image_data), filename="regenerated_image.png")
            await interaction.followup.send(file=file, view=self)
            logger.info(f"Image régénérée et envoyée à {interaction.user.display_name}")
            if not self.private and self.safe:
                await gallery(interaction.client, image_data, self.prompt, interaction)
        else:
            await interaction.followup.send("Echec de la régénération de l'image. Veuillez réessayer.")
            logger.error(f"Échec de la régénération d'image pour {interaction.user.display_name}")
