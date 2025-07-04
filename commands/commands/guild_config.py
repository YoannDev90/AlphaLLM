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

async def setup(bot: discord.Client):
    @bot.tree.command(name="guild-config", description="Configure server language and announcement channel")
    @app_commands.describe(
        langue="Language for the server",
        announce_channel="Channel for bot announcements"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.choices(langue=LANG_CHOICES)
    async def guild_config(
        interaction: discord.Interaction,
        langue: Optional[app_commands.Choice[str]] = None,
        announce_channel: Optional[discord.TextChannel] = None,
    ):
        logger.info(f"Commande /guild-config executed by {interaction.user.display_name}")
        await interaction.response.defer()

        update_data = {"id_discord": interaction.guild.id}
        summary = []

        if langue is not None:
            update_data["lang"] = langue.value
            summary.append(f"🌍 **Language:** {langue.name}")

        if announce_channel is not None:
            update_data["announce_channel"] = announce_channel.id
            summary.append(f"📢 **Announcement Channel:** {announce_channel.mention}")

        if len(update_data) == 1:
            await interaction.followup.send("⚠️ No parameter provided. Nothing updated.", ephemeral=True)
            return
        
        try:
            supabase.table("server_settings").upsert(update_data).execute()

            summary_text = "\n".join(summary)
            if not summary_text:
                summary_text = "No changes made."

            embed = discord.Embed(
                title="✅ Configuration updated",
                description=summary_text,
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_footer(text=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"Guild config updated for {interaction.guild.name}: {update_data}")
        except Exception as e:
            logger.error(f"Error updating guild config: {str(e)}")
            await interaction.followup.send("❌ An error occurred while updating the settings.", ephemeral=True)

    # Commande /gc (alias de /guild-config) pour configurer le serveur
    
    @bot.tree.command(name="gc", description="Configure server language and announcement channel")
    @app_commands.describe(
        langue="Language for the server",
        announce_channel="Channel for bot announcements"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.choices(langue=LANG_CHOICES)
    async def guild_config_alias(
        interaction: discord.Interaction,
        langue: Optional[app_commands.Choice[str]] = None,
        announce_channel: Optional[discord.TextChannel] = None,
    ):
        await guild_config(interaction, langue, announce_channel)
