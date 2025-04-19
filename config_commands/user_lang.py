import discord
from discord import app_commands
from supabase import Client, create_client, ClientOptions
from utils.langs import get_language, get_translation as tlt
import os
import logging

logger = logging.getLogger('AlphaLLM')

# Configuration Supabase
supabase = Client(
    os.getenv("DB_URL"),
    os.getenv("DB_KEY"),
    options=ClientOptions(headers={"Authorization": f"Bearer {os.getenv('JWT_KEY')}"})
)

async def setup(bot: discord.Client):
    @bot.tree.command(name="user-lang", description="Define your personal language")
    @app_commands.choices(langue=[
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
    ])
    async def langue(interaction: discord.Interaction, langue: app_commands.Choice[str]):
        try:
            # Mise à jour dans Supabase
            supabase.table("users_settings").upsert({
                "id_discord": interaction.user.id,
                "lang": langue.value
            }).execute()

            user_lang = get_language(interaction.user.id)

            embed = discord.Embed(
                title="🌍" + tlt(language=user_lang, key="lang_embed_title"),
                description= tlt(language=user_lang, key="lang_embed_description", langue_s=langue.value.upper()),
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Langue mise à jour pour {interaction.user.display_name} : {langue.value}")

        except Exception as e:
            logger.error(f"Erreur mise à jour langue : {str(e)}")
            await interaction.response.send_message("❌" + tlt(language=user_lang, key="lang_settings_error"), ephemeral=True)