import discord
from discord import app_commands
from typing import Optional
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
    @bot.tree.command(name="guild-announce-channel", description="Define the channel for bot announcements")
    async def announce_channel(interaction: discord.Interaction, channel: Optional[discord.TextChannel]):
        try:

            supabase.table("server_settings").upsert({
                "id_discord": interaction.guild.id,
                "announce_channel": channel.id if channel else None
            }).execute()

            user_lang = get_language(interaction.user.id)

            embed = discord.Embed(
                title="📢 Successfully updated",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Announcement channel mis à jour pour {interaction.guild.name} : {channel.name if channel else 'None'}")

        except Exception as e:
            logger.error(f"Erreur mise à jour salon des annonces : {str(e)}")
            await interaction.response.send_message("❌ ERROR", ephemeral=True)
