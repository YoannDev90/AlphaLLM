import discord
from discord import app_commands
from typing import Optional
from utils.database import get_supabase_client
import logging
from datetime import datetime
from utils.config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
supabase = get_supabase_client()

LANG_CHOICES = [
    app_commands.Choice(name="Français 🇫🇷", value="FR"),
    app_commands.Choice(name="English 🇬🇧", value="EN"),
    app_commands.Choice(name="Español 🇪🇸", value="ES"),
    app_commands.Choice(name="Deutsch 🇩🇪", value="DE"),
    app_commands.Choice(name="Italiano 🇮🇹", value="IT"),
    app_commands.Choice(name="Português 🇧🇷", value="PT"),
    app_commands.Choice(name="Nederlands 🇳🇱", value="NL"),
    app_commands.Choice(name="Русский 🇷🇺", value="RU"),
    app_commands.Choice(name="日本語 🇯🇵", value="JA"),
    app_commands.Choice(name="한국어 🇰🇷", value="KO"),
    app_commands.Choice(name="中文 🇨🇳", value="ZH"),
    app_commands.Choice(name="العربية 🇸🇦", value="AR"),
]

IMAGE_MODEL_CHOICES = [
    app_commands.Choice(name="Flux", value="flux"),
    app_commands.Choice(name="Turbo", value="turbo")
]

IMAGE_PRIVATE_CHOICES = [
    app_commands.Choice(name="Yes ✅", value=1),
    app_commands.Choice(name="No ❌", value=0)
]

IMAGE_ENHANCE_CHOICES = [
    app_commands.Choice(name="Yes ✅", value=1),
    app_commands.Choice(name="No ❌", value=0)
]

async def setup(bot: discord.Client):
    @bot.tree.command(name="user-config", description="Configure user language and preferences, image settings, and audio settings")
    @app_commands.choices(langue=LANG_CHOICES, image_model=IMAGE_MODEL_CHOICES, image_private=IMAGE_PRIVATE_CHOICES, image_enhance=IMAGE_ENHANCE_CHOICES)
    @app_commands.describe(
        langue="Language for the user",
        perso_preprompt="Personal preprompt for text generation"
    )
    async def user_config(
        interaction: discord.Interaction,
        langue: Optional[app_commands.Choice[str]] = None,
        image_model: Optional[app_commands.Choice[str]] = None,
        image_size: Optional[str] = None,
        image_private: Optional[app_commands.Choice[int]] = None,
        image_enhance: Optional[app_commands.Choice[int]] = None,
        perso_preprompt: Optional[str] = None,
    ):
        logger.info(f"Commande /user-config executed by {interaction.user.display_name}")
        await interaction.response.defer(thinking=True, ephemeral=True)

        update_data = {}
        summary = []

        if langue is not None:
            update_data["lang"] = langue.value
            summary.append(f"🌍 **Language:** {langue.name}")

        if image_model is not None:
            update_data["image_model"] = image_model.value
            summary.append(f"🛠️ **Model:** {image_model.name}")

        if image_size is not None:
            update_data["image_size"] = image_size
            summary.append(f"📏 **Size:** {image_size}")

        if image_private is not None:
            update_data["image_private"] = True if image_private.value == 1 else False
            summary.append(f"🔒 **Private:** {'Yes' if update_data['image_private'] else 'No'}")

        if image_enhance is not None:
            update_data["image_enhance"] = True if image_enhance.value == 1 else False
            summary.append(f"✨ **Enhance:** {'Yes' if update_data['image_enhance'] else 'No'}")

        if perso_preprompt is not None:
            update_data["perso_preprompt"] = perso_preprompt
            summary.append(f"📝 **Personal Preprompt:** {perso_preprompt}")

        if len(update_data) == 0:
            await interaction.followup.send("⚠️ No parameter provided. Nothing updated.", ephemeral=True)
            return

        try:
            insert_data = {
                    "name": interaction.user.global_name if interaction.user.global_name else interaction.user.name,
                    "modified": datetime.now().isoformat(),
                    **update_data
                }
            result = supabase.table("users_settings").update(insert_data).eq("id_discord", interaction.user.id).execute()
            if not result.data:
                logger.info(f"No existing record found for user {interaction.user.id}, inserting new record")
                insert_data = {
                    "id_discord": interaction.user.id,
                    "name": interaction.user.global_name if interaction.user.global_name else interaction.user.name,
                    "modified": datetime.now().isoformat(),
                    **update_data
                }
                result = supabase.table("users_settings").insert(insert_data).execute()
                print(f"Insert result: {result}")

            summary_text = "\n".join(summary)
            if not summary_text:
                summary_text = "No changes made."

            embed = discord.Embed(
                title="✅ Configuration updated",
                description=summary_text,
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"User config updated for {interaction.user.display_name}")
            
        except Exception as e:
            logger.error(f"Error updating user config: {str(e)}")
            await interaction.followup.send("❌ An error occurred while updating the settings.", ephemeral=True)
            return
