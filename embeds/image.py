import discord
import logging
from io import BytesIO
from utils.config import logger_name, TIMEOUT_IMAGE_VIEW

logger = logging.getLogger(logger_name)

class ImageView(discord.ui.View):
    def __init__(self, prompt, model, size, enhance, safe):
        super().__init__(timeout=TIMEOUT_IMAGE_VIEW)
        self.prompt = prompt
        self.model = model
        self.size = size
        self.enhance = enhance
        self.safe = safe
        self.message = None

    async def on_timeout(self):
        """Supprime les boutons lorsque la vue expire après 30 secondes"""
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass

    @discord.ui.button(emoji="🔄", label="Regenerate", style=discord.ButtonStyle.gray)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Regénération d'image demandée par {interaction.user.display_name}")
        await interaction.response.defer()
        
        # Import des fonctions nécessaires à l'exécution
        from utils.user_manager import new_interaction, new_image
        from utils.image_gen import generate_image
        
        new_interaction(interaction.user.id)
        new_image(interaction.user.id)
        
        image_data, nsfw = await generate_image(self.prompt, self.model, self.size)
        
        if image_data:
            file = discord.File(BytesIO(image_data), filename="regenerated_image.png")
            view = ImageView(self.prompt, self.model, self.size, self.enhance, not nsfw)
            message = await interaction.followup.send("🔄 Regenerated image:", file=file, view=view)
            view.message = message
            logger.info(f"Image régénérée et envoyée à {interaction.user.display_name}")
        else:
            await interaction.followup.send("❌ Image regeneration failed.", delete_after=10)
            logger.error(f"Échec de la régénération d'image pour {interaction.user.display_name}")

    @discord.ui.button(emoji="✏️", label="Edit", style=discord.ButtonStyle.gray)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Édition d'image demandée par {interaction.user.display_name}")
        
        # Import des fonctions nécessaires à l'exécution
        from utils.user_manager import new_interaction, new_image
        
        new_interaction(interaction.user.id)
        new_image(interaction.user.id)
        url = self.message.attachments[0].url if self.message and self.message.attachments else None

        modal = EditImageModal(self.prompt, url, self.size, self.enhance)
        await interaction.response.send_modal(modal)

    @discord.ui.button(emoji="👁️", label="Hide", style=discord.ButtonStyle.gray)
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Masquage d'image demandé par {interaction.user.display_name}")
        await interaction.response.defer()
        updated_attachments = [
            discord.File(BytesIO(await attachment.read()), filename=f"SPOILER_{attachment.filename}")
            for attachment in interaction.message.attachments
        ]
        
        await interaction.message.edit(attachments=updated_attachments)

    @discord.ui.button(emoji="📌", label="Pin", style=discord.ButtonStyle.gray)
    async def pin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel.permissions_for(interaction.user).manage_messages:
            await interaction.response.send_message("You do not have permission to pin messages.", ephemeral=True)
            return
        logger.info(f"Epinglage d'image demandé par {interaction.user.display_name}")
        await interaction.response.defer()
        await interaction.message.pin()
        await interaction.followup.send("Image pinned.", delete_after=2)

    @discord.ui.button(emoji="🗑️", label="Delete", style=discord.ButtonStyle.gray)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"Suppression d'image demandée par {interaction.user.display_name}")
        await interaction.message.edit(view=None)
        await interaction.message.delete()


class EditImageModal(discord.ui.Modal):
    def __init__(self, original_prompt, url, size, enhance):
        super().__init__(title="Edit Image Prompt")
        self.original_prompt = original_prompt
        self.url = url
        self.size = size
        self.enhance = enhance
        
        self.prompt_input = discord.ui.TextInput(
            label="New prompt for image editing",
            placeholder="Enter the modifications you want to make to the image...",
            style=discord.TextStyle.paragraph,
            max_length=1024,
            required=True
        )
        self.add_item(self.prompt_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Import des fonctions nécessaires à l'exécution
        from utils.image_gen import image_edit
        
        edit_prompt = self.prompt_input.value
        
        if not self.url:
            await interaction.followup.send("❌ No image to edit found.", delete_after=10)
            return
        
        image_data, nsfw = await image_edit(edit_prompt, self.url, self.size)
        
        if image_data:
            file = discord.File(BytesIO(image_data), filename="edited_image.png")
            view = ImageView(edit_prompt, "kontext", self.size, self.enhance, not nsfw)
            message = await interaction.followup.send("✏️ Edited image:", file=file, view=view)
            view.message = message
            logger.info(f"Image éditée et envoyée à {interaction.user.display_name}")
        else:
            await interaction.followup.send("❌ Image editing failed.", delete_after=10)
            logger.error(f"Échec de l'édition d'image pour {interaction.user.display_name}")
