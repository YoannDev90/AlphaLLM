import discord
from discord import app_commands
from utils.image_gen import generate_image
from utils.user_config import get_image_model, get_image_size, get_image_private, get_image_enhance
from utils.user_manager import new_interaction, new_image
from utils.langs import get_language, get_translation as tlt
from io import BytesIO
from utils.gallery import gallery
import logging
import random
import os

logger = logging.getLogger('AlphaLLM')

PUBLIC_IMAGE_CHANNEL_ID = os.getenv("GALERIE_ID")

async def setup(bot: discord.Client):
    @bot.tree.command(name="multimage", description="Génère plusieurs images à partir d'un prompt")
    @app_commands.choices(model=[
        app_commands.Choice(name="Flux (by BlackForestLabs)", value="flux"),
        app_commands.Choice(name="SDXL (by Stability.AI)", value="turbo")
    ])
    async def multimage(
        interaction: discord.Interaction,
        prompt: str,
        number: int = 2,
        model: str = None,
        size: str = None,
        private: bool = None,
        enhance: bool = None,
    ):
        logger.info(f"Commande multimage exécutée par {interaction.user.display_name}")

        # Récupérer la langue de l'utilisateur
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
        
        if number > 4:
            await interaction.response.send_message(tlt(language=user_lang, key="too_many_imgs"), ephemeral=True)
            logger.warning(f"Nombre d'images trop grand pour {interaction.user.display_name}")
            number = 4

        await interaction.response.send_message(tlt(language=user_lang, key="generating_in_progress"), delete_after=25)
        interaction_channel = interaction.channel

        nologo = True
        safe = True if interaction.guild and interaction.guild.nsfw_level == discord.NSFWLevel.default and not interaction.channel.is_nsfw() else False
        new_interaction(interaction.user.id)
        new_image(interaction.user.id, count=number)

        for i in range(number):
            seed = random.randint(0, 1000000)
            image_data = await generate_image(prompt, model, seed, width, height, nologo, private, enhance, safe)
            
            if image_data:
                file_img = discord.File(BytesIO(image_data), filename=f"generated_image_{i+1}.png")
                logger.info(f"Image {i+1}/{number} générée et envoyée à {interaction.user.display_name}")
                if not private and safe:
                    await gallery(bot, image_data, prompt, interaction)
            else:
                await interaction.followup.send(tlt(language=user_lang, key="multimage_error", num=i+1))
                logger.error(f"Échec de la génération de l'image {i+1} pour {interaction.user.display_name}")

            view = MultiImageView(prompt, model, width, height, nologo, private, enhance, safe, user_lang)
            await interaction_channel.send(file=file_img, view=view)


class MultiImageView(discord.ui.View):
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
        logger.info(f"Regénération d'images demandée par {interaction.user.display_name}")
        await interaction.response.defer()
        seed = random.randint(0, 1000000)
        new_interaction(interaction.user.id)
        new_image(interaction.user.id, 1)

        image_data = await generate_image(self.prompt, self.model, seed, self.width, self.height, self.nologo, self.private, self.enhance, self.safe)
            
        if image_data:
            file_img = discord.File(BytesIO(image_data), filename=f"regenerated_image.png")
            logger.info(f"Image régénérée et envoyée à {interaction.user.display_name}")
            if not self.private and self.safe:
                await gallery(interaction.client, image_data, self.prompt, interaction)
        else:
            await interaction.followup.send(tlt(language=self.user_lang, key="image_regen_error"))
            logger.error(f"Échec de la régénération de l'image pour {interaction.user.display_name}")

        await interaction.followup.send(file=file_img, view=self)

    @discord.ui.button(emoji="👁️", style=discord.ButtonStyle.green)
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Masquage d'images demandé par {interaction.user.display_name}")
        await interaction.response.defer()
        updated_attachments = [
            discord.File(BytesIO(await attachment.read()), filename=f"SPOILER_{attachment.filename}")
            for attachment in interaction.message.attachments
        ]
        
        await interaction.message.edit(attachments=updated_attachments)

    @discord.ui.button(emoji="📌", style=discord.ButtonStyle.gray)
    async def pin(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Epinglage d'images demandé par {interaction.user.display_name}")
        await interaction.response.defer()
        await interaction.message.pin()
        await interaction.followup.send(tlt(language=self.user_lang, key="image_pinned"), ephemeral=True)

    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Suppression d'images demandée par {interaction.user.display_name}")
        await interaction.message.delete()
