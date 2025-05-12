import discord
from discord import app_commands
from typing import Optional
from supabase import Client, ClientOptions, create_client
from utils.langs import get_language, get_translation as tlt
import os
import logging

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
    app_commands.Choice(name="हिन्दी 🇮🇳", value="HI")
]

IMAGE_MODEL_CHOICES = [
    app_commands.Choice(name="Flux (by BlackForestLabs)", value="flux"),
    app_commands.Choice(name="SDXL (by Stability.AI)", value="turbo")
]

IMAGE_PRIVATE_CHOICES = [
    app_commands.Choice(name="Yes ✅", value=1),
    app_commands.Choice(name="No ❌", value=0)
]

IMAGE_ENHANCE_CHOICES = [
    app_commands.Choice(name="Yes ✅", value=1),
    app_commands.Choice(name="No ❌", value=0)
]

IMAGE_SIZE_CHOICES = [
    app_commands.Choice(name="512x512", value="512x512"),
    app_commands.Choice(name="640x640", value="640x640"),
    app_commands.Choice(name="768x768", value="768x768"),
    app_commands.Choice(name="896x896", value="896x896"),
    app_commands.Choice(name="960x960", value="960x960"),
    app_commands.Choice(name="1024x1024", value="1024x1024"),
    app_commands.Choice(name="1280x1280", value="1280x1280"),
    app_commands.Choice(name="1408x1408", value="1408x1408"),
    app_commands.Choice(name="1536x1536", value="1536x1536"),
    app_commands.Choice(name="1792x1792", value="1792x1792"),
    app_commands.Choice(name="1920x1920", value="1920x1920"),
    app_commands.Choice(name="2048x2048", value="2048x2048")
]

AUDIO_GEN_CHOICES = [
    app_commands.Choice(name="Yes ✅", value=1),
    app_commands.Choice(name="No ❌", value=0)
]

AUDIO_VOICE_CHOICES = [
    app_commands.Choice(name="English 🇬🇧", value="en"),
    app_commands.Choice(name="Français 🇫🇷", value="fr"),
]

ANNOUNE_MP_CHOICES = [
    app_commands.Choice(name="Yes ✅", value=1),
    app_commands.Choice(name="No ❌", value=0)
]

async def setup(bot: discord.Client):
    @bot.tree.command(name="user-config", description="Configure user language and preferences, image settings, and audio settings")
    @app_commands.choices(langue=LANG_CHOICES, image_model=IMAGE_MODEL_CHOICES, image_private=IMAGE_PRIVATE_CHOICES, image_enhance=IMAGE_ENHANCE_CHOICES, image_size=IMAGE_SIZE_CHOICES, audio_gen=AUDIO_GEN_CHOICES, audio_voice=AUDIO_VOICE_CHOICES, announce_mp=ANNOUNE_MP_CHOICES)
    async def user_config(
        interaction: discord.Interaction,
        langue: Optional[app_commands.Choice[str]] = None,
        image_model: Optional[app_commands.Choice[str]] = None,
        image_size: Optional[app_commands.Choice[str]] = None,
        image_private: Optional[app_commands.Choice[int]] = None,
        image_enhance: Optional[app_commands.Choice[int]] = None,
        audio_gen: Optional[app_commands.Choice[int]] = None,
        audio_voice: Optional[app_commands.Choice[str]] = None,
        announce_mp: Optional[app_commands.Choice[int]] = None,
        perso_preprompt: Optional[str] = None,
    ):
        logger.info(f"/user-config executed by {interaction.user.display_name}")
        await interaction.response.defer(thinking=True, ephemeral=True)

        # Build the update dict only with provided parameters
        #update_data = {"id_discord": interaction.guild.id}
        update_data = {}
        summary = []

        if langue is not None:
            update_data["lang"] = langue.value
            summary.append(f"🌍 **Language:** {langue.name}")

        if image_model is not None:
            update_data["image_model"] = image_model.value
            summary.append(f"🛠️ **Model:** {image_model.name}")

        if image_size is not None:
            update_data["image_size"] = image_size.value
            summary.append(f"📏 **Size:** {image_size.name}")

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

            user_lang = get_language(interaction.user.id)

            embed = discord.Embed(
                title="✅ Configuration updated",
                description="\n".join(summary) if summary else "No changes made.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"User config updated for {interaction.user.display_name}: {update_data}")
        except Exception as e:
            logger.error(f"Error updating user config: {str(e)}")
            await interaction.followup.send("❌ An error occurred while updating the settings.", ephemeral=True)
