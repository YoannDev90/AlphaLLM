import discord
from discord import app_commands
from typing import Optional
from dotenv import load_dotenv
from supabase import Client, ClientOptions, create_client
import os
import logging

load_dotenv()

logger = logging.getLogger('AlphaLLM')

url: str = os.environ.get("DB_URL").encode('utf-8').decode('unicode-escape')
key: str = os.environ.get("DB_KEY").encode('utf-8').decode('unicode-escape')
jwt: str = os.environ.get("JWT_KEY").encode('utf-8').decode('unicode-escape')
supabase: Client = create_client(url, key, 
                                options=ClientOptions(
                                    schema="public",
                                    headers={"Authorization": f"Bearer {jwt}"},
                                    auto_refresh_token=True,
                                    persist_session=True
                                ))

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
        image_model="Model for image generation",
        image_size="Size for image generation (e.g., 1024x2048, min 256x256, max 2048x2048)",
        image_private="Private image generation",
        image_enhance="Enhance image generation",
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
            try:
                supabase.table("users_settings").update(update_data).eq("id_discord", interaction.user.id).execute()
            except Exception as e:
                logger.error(f"Error updating user config: {str(e)}")

                try:
                    supabase.table("users_settings").insert({"id_discord": interaction.user.id, **update_data}).execute()
                except Exception as e:
                    logger.error(f"Error inserting user config: {str(e)}")
                    await interaction.followup.send("❌ An error occurred while inserting the settings.", ephemeral=True)

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
            logger.info(f"User config updated for {interaction.user.display_name}: {update_data}")
        except Exception as e:
            logger.error(f"Error updating user config: {str(e)}")
            await interaction.followup.send("❌ An error occurred while updating the settings.", ephemeral=True)

    # Commande /uc (alias de /user-config) pour configurer l'utilisateur
    
    @bot.tree.command(name="uc", description="Configure user language and preferences, image settings, and audio settings")
    @app_commands.choices(langue=LANG_CHOICES, image_model=IMAGE_MODEL_CHOICES, image_private=IMAGE_PRIVATE_CHOICES, image_enhance=IMAGE_ENHANCE_CHOICES)
    @app_commands.describe(
        langue="Language for the user",
        image_model="Model for image generation",
        image_size="Size for image generation (e.g., 1024x2048, min 256x256, max 2048x2048)",
        image_private="Private image generation",
        image_enhance="Enhance image generation",
        perso_preprompt="Personal preprompt for text generation"
    )
    async def user_config_alias(
        interaction: discord.Interaction,
        langue: Optional[app_commands.Choice[str]] = None,
        image_model: Optional[app_commands.Choice[str]] = None,
        image_size: Optional[str] = None,
        image_private: Optional[app_commands.Choice[int]] = None,
        image_enhance: Optional[app_commands.Choice[int]] = None,
        perso_preprompt: Optional[str] = None,
    ):
        await user_config(interaction, langue, image_model, image_size, image_private, image_enhance, perso_preprompt)
