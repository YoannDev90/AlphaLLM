import discord
from discord import app_commands
from utils.image_gen import generate_image
from utils.gallery import gallery
from io import BytesIO
import logging
from dotenv import load_dotenv
from utils.langs import get_language, get_translation as tlt
from utils.user_config import get_image_model, get_image_size, get_image_private, get_image_enhance
from utils.user_manager import new_interaction, new_image
from utils.server_config import get_allow_nsfw
import random

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="image", description="Génère une image à partir d'un prompt")
    @app_commands.choices(model=[
        app_commands.Choice(name="Flux (by BlackForestLabs)", value="flux"),
        app_commands.Choice(name="SDXL (by Stability.AI)", value="turbo")
    ])
    async def image(
        interaction: discord.Interaction,
        prompt: str,
        model: str = None,
        size: str = None,
        private: bool = None,
        enhance: bool = None,
    ):
        await interaction.response.defer()

        logger.info(f"Commande image exécutée par {interaction.user.display_name}")

        user_lang = get_language(interaction.user.id)

        model = get_image_model(interaction.user.id) if model is None else model
        size = get_image_size(interaction.user.id) if size is None else size
        private = get_image_private(interaction.user.id) if private is None else private
        enhance = get_image_enhance(interaction.user.id) if enhance is None else enhance

        width, height = map(int, size.split("x"))
    
        if width > 2048 or height > 2048:
            logger.warning(f"Dimensions de l'image trop grandes pour {interaction.user.display_name}")
            width = 2048
            height = 2048

        seed = None
        nologo = True
        safe = True if interaction.guild and interaction.guild.nsfw_level == discord.NSFWLevel.default and not interaction.channel.is_nsfw() else False
        safe = get_allow_nsfw(interaction.guild.id)  if get_allow_nsfw(interaction.guild.id) else True
        new_interaction(interaction.user.id)
        new_image(interaction.user.id)
        image_data = await generate_image(prompt, model, seed, width, height, nologo, private, enhance, safe)
    
        if image_data:
            file = discord.File(BytesIO(image_data), filename="generated_image.png")
            view = ImageView(prompt, model, width, height, nologo, private, enhance, safe, user_lang)
            await interaction.followup.send(file=file, view=view)
            logger.info(f"Image générée et envoyée à {interaction.user.display_name}")
            if not private and safe:
                await gallery(bot, image_data, prompt, interaction)
        else:
            view = RetryImageView(prompt, model, width, height, nologo, private, enhance, safe, user_lang)
            await interaction.followup.send(tlt(language=user_lang, key="image_gen_error"), delete_after=10, view=view)
            logger.error(f"Échec de la génération d'image pour {interaction.user.display_name}")


class ImageView(discord.ui.View):
    def __init__(self, prompt, model, width, height, nologo, private, enhance, safe, user_lang):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.width = width
        self.height = height
        self.nologo = nologo
        self.private = private
        self.enhance = enhance
        self.safe = safe
        self.user_lang = user_lang

    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.blurple)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Regénération d'image demandée par {interaction.user.display_name}")
        await interaction.response.defer()
        seed = random.randint(0, 1000000)
        new_interaction(interaction.user.id)
        new_image(interaction.user.id)
        image_data = await generate_image(self.prompt, self.model, seed, self.width, self.height, self.nologo, self.private, self.enhance, self.safe)
        
        if image_data:
            file = discord.File(BytesIO(image_data), filename="regenerated_image.png")
            await interaction.followup.send(file=file, view=self)
            logger.info(f"Image régénérée et envoyée à {interaction.user.display_name}")
            if not self.private and self.safe:
                await gallery(interaction.client, image_data, self.prompt, interaction)
        else:
            await interaction.followup.send(tlt(language=self.user_lang, key="image_regen_error"), delete_after=10)
            logger.error(f"Échec de la régénération d'image pour {interaction.user.display_name}")

    @discord.ui.button(emoji="👁️", style=discord.ButtonStyle.green)
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Masquage d'image demandé par {interaction.user.display_name}")
        await interaction.response.defer()
        updated_attachments = [
            discord.File(BytesIO(await attachment.read()), filename=f"SPOILER_{attachment.filename}")
            for attachment in interaction.message.attachments
        ]
        
        await interaction.message.edit(attachments=updated_attachments)

    @discord.ui.button(emoji="📌", style=discord.ButtonStyle.gray)
    async def pin(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Epinglage d'image demandé par {interaction.user.display_name}")
        await interaction.response.defer()
        await interaction.message.pin()
        await interaction.followup.send(tlt(language=self.user_lang, key="image_pinned"), ephemeral=True)

    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Suppression d'image demandée par {interaction.user.display_name}")
        await interaction.message.delete()


class RetryImageView(discord.ui.View):
    def __init__(self, prompt, model, width, height, nologo, private, enhance, safe, user_lang):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.width = width
        self.height = height
        self.nologo = nologo
        self.private = private
        self.enhance = enhance
        self.safe = safe
        self.user_lang = user_lang

    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.blurple)
    async def retry(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Nouvelle tentative de génération d'image demandée par {interaction.user.display_name}")
        await interaction.response.defer()
        seed = random.randint(0, 1000000)
        image_data = await generate_image(self.prompt, self.model, seed, self.width, self.height, self.nologo, self.private, self.enhance, self.safe)
        
        if image_data:
            file = discord.File(BytesIO(image_data), filename="generated_image.png")
            await interaction.followup.send(file=file, view=self)
            logger.info(f"Image générée et envoyée à {interaction.user.display_name}")
            if not self.private and self.safe:
                await gallery(interaction.client, image_data, self.prompt, interaction)
        else:
            await interaction.followup.send(tlt(language=self.user_lang, key="image_gen_error"), delete_after=10)
            logger.error(f"Échec de la génération d'image pour {interaction.user.display_name}")
