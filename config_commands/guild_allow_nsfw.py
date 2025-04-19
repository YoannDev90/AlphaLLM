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
    @bot.tree.command(name="guild-allow-nsfw", description="Define if users can generate NSFW content")
    @app_commands.choices(allow=[
        app_commands.Choice(name="Yes ✅", value=1),
        app_commands.Choice(name="No ❌", value=0)
    ])
    async def allow_nsfw(interaction: discord.Interaction, allow: app_commands.Choice[int]):
        allowed = True if allow.value == 1 else False
        try:
            supabase.table("server_settings").upsert({
                "id_discord": interaction.guild.id,
                "allow_nsfw": allowed
            }).execute()

            await interaction.response.send_message("✅ Updated", ephemeral=True)
            logger.info(f"Allow NSFW content mis à jour pour {interaction.guild.name} : {allow.value}")

        except Exception as e:
            logger.error(f"Erreur mise à jour NSFW : {str(e)}")
            await interaction.response.send_message("❌ ERROR", ephemeral=True)