import discord
from discord import app_commands
from utils.image_gen import generate_image
from utils.gallery import gallery
from io import BytesIO
import logging
from utils.user_config import get_image_model, get_image_size, get_image_private, get_image_enhance
from utils.user_manager import new_interaction, new_image
from utils.server_config import get_allow_nsfw
from utils.ai_mod import is_nsfw
from utils.database import get_blacklist
import random

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="image", description="Generate an image from a prompt")
    @app_commands.describe(
        prompt="The prompt to generate the image from",
        model="The model to use for image generation (default: flux)",
        size="The size of the image (default: 1024x1024)",
        private="Whether the image should be private (default: No)",
        enhance="Whether to enhance the image (default: No)"
    )
    @app_commands.choices(model=[
        app_commands.Choice(name="Flux", value="flux"),
        app_commands.Choice(name="GPT Image", value="gptimage"),
        app_commands.Choice(name="Kontext", value="kontext"),
        app_commands.Choice(name="Turbo", value="turbo")
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


        blacklist_data = get_blacklist()
                
        # Vérifier si l'utilisateur est sur la liste noire et récupérer le motif
        blacklist_entry = next((entry for entry in blacklist_data if entry.get('id_discord') == interaction.user.id), None)
        if blacklist_entry:
            reason = blacklist_entry.get('reason', 'Unspecified')
            logger.info(f"Génération d'image de {interaction.user.display_name} (ID: {interaction.user.id}) ignorée - Liste noire - Motif: {reason}")
            await interaction.followup.send(f"⛔️ You are blacklisted from the bot (<@{interaction.user.id}>) - Reason: **{reason}**")
            return
        
        logger.info(f"Commande /image exécutée par {interaction.user.display_name} ({interaction.user.id})")

        model = get_image_model(interaction.user.id) if model is None else model
        model = model if model is not None else 'flux'

        size = get_image_size(interaction.user.id) if size is None else size
        size = size if size is not None else '1024x1024'

        private = get_image_private(interaction.user.id) if private is None else private
        private = private if private is not None else False

        enhance = get_image_enhance(interaction.user.id) if enhance is None else enhance
        enhance = enhance if enhance is not None else False

        width, height = map(int, size.split("x"))

        if width > 2048 or height > 2048:
            logger.warning(f"Dimensions de l'image trop grandes pour {interaction.user.display_name}")
            width = 2048
            height = 2048

        safe = False

        new_interaction(interaction.user.id)
        new_image(interaction.user.id)
        image_data, nsfw = await generate_image(prompt, model, None, width, height, private, enhance, safe)

        if nsfw and not interaction.channel.is_nsfw():
            logger.warning(f"Image NSFW générée par {interaction.user.display_name} dans un canal non NSFW")
            await interaction.followup.send("🔞 This image is NSFW and cannot be sent in a non-NSFW channel.")
            return
    
        else:
            if image_data:
                file = discord.File(BytesIO(image_data), filename="generated_image.png")
                view = ImageView(prompt, model, width, height, private, enhance, safe)
                message = await interaction.followup.send(file=file, view=view)
                view.message = message
                logger.info(f"Image générée et envoyée à {interaction.user.display_name}")
                if not private and not nsfw:
                    await gallery(bot, image_data, prompt, interaction.user.display_name)
            else:
                view = RetryImageView(prompt, model, width, height, private, enhance, safe)
                message = await interaction.followup.send("❌ Image generation failed.", view=view)
                view.message = message
                logger.error(f"Échec de la génération d'image pour {interaction.user.display_name}")


class ImageView(discord.ui.View):
    def __init__(self, prompt, model, width, height, private, enhance, safe):
        super().__init__(timeout=30.0)
        self.prompt = prompt
        self.model = model
        self.width = width
        self.height = height
        self.private = private
        self.enhance = enhance
        self.safe = safe
        self.message = None

    async def on_timeout(self):
        """Supprime les boutons lorsque la vue expire après 30 secondes"""
        if self.message:
            try:
                await self.message.edit(view=None)
            except:
                logger.warning("Impossible de supprimer les boutons après expiration")

    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.blurple)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Regénération d'image demandée par {interaction.user.display_name}")
        await interaction.response.defer()
        seed = random.randint(0, 1000000)
        new_interaction(interaction.user.id)
        new_image(interaction.user.id)
        image_data = await generate_image(self.prompt, self.model, seed, self.width, self.height, self.private, self.enhance, self.safe)
        
        if image_data:
            file = discord.File(BytesIO(image_data), filename="regenerated_image.png")
            view = ImageView(self.prompt, self.model, self.width, self.height, self.private, self.enhance, self.safe)
            message = await interaction.followup.send(file=file, view=view)
            view.message = message
            logger.info(f"Image régénérée et envoyée à {interaction.user.display_name}")
            if not self.private and self.safe:
                await gallery(interaction.client, image_data, self.prompt, interaction)
        else:
            await interaction.followup.send("Image regeneration failed.", delete_after=10)
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
        if not interaction.channel.permissions_for(interaction.user).manage_messages:
            await interaction.response.send_message("You do not have permission to pin messages.", ephemeral=True)
            return
        logger.info(f"Epinglage d'image demandé par {interaction.user.display_name}")
        await interaction.response.defer()
        await interaction.message.pin()
        await interaction.followup.send("Image pinned.", delete_after=2)

    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Suppression d'image demandée par {interaction.user.display_name}")
        await interaction.message.delete()


class RetryImageView(discord.ui.View):
    def __init__(self, prompt, model, width, height, private, enhance, safe):
        super().__init__(timeout=30.0)
        self.prompt = prompt
        self.model = model
        self.width = width
        self.height = height
        self.private = private
        self.enhance = enhance
        self.safe = safe
        self.message = None
        
    async def on_timeout(self):
        """Supprime les boutons lorsque la vue expire après 30 secondes"""
        if self.message:
            try:
                await self.message.edit(view=None)
            except:
                pass

    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.blurple)
    async def retry(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Nouvelle tentative de génération d'image demandée par {interaction.user.display_name}")
        await interaction.response.defer()
        seed = random.randint(0, 1000000)
        image_data = await generate_image(self.prompt, self.model, seed, self.width, self.height, self.private, self.enhance, self.safe)

        if image_data:
            file = discord.File(BytesIO(image_data), filename="generated_image.png")
            view = ImageView(self.prompt, self.model, self.width, self.height, self.private, self.enhance, self.safe)
            message = await interaction.followup.send(file=file, view=view)
            view.message = message
            logger.info(f"Image générée et envoyée à {interaction.user.display_name}")
            if not self.private and self.safe:
                await gallery(interaction.client, image_data, self.prompt, interaction)
        else:
            await interaction.followup.send("❌ Image generation failed.", delete_after=10)
            logger.error(f"Échec de la génération d'image pour {interaction.user.display_name}")
