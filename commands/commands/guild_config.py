import discord
from discord import app_commands
from typing import Optional
from embeds.config import ChannelSelectView, RoleSelectView
from langs.language_manager import language_manager
from utils import get_guild_language
from utils.database import get_supabase_client
import logging
from utils.config import LOGGER_NAME
from datetime import datetime

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
    app_commands.Choice(name="हिंदी 🇮🇳", value="HI"),
    app_commands.Choice(name="Bahasa Indonesia 🇮🇩", value="ID"),
    app_commands.Choice(name="Polski 🇵🇱", value="PL"),
]

ALLOWED_CHANNELS = [
    app_commands.Choice(name="Allow every channel", value="every"),
    app_commands.Choice(name="Allow specific channels", value="specific"),
]

ALLOWED_ROLES = [
    app_commands.Choice(name="Allow every role, including @everyone", value="every"),
    app_commands.Choice(name="Allow specific roles", value="specific"),
]

def get_guild_lang_code(guild_id):
    """Récupère le code langue du serveur et le convertit pour le gestionnaire de langues"""
    guild_lang = get_guild_language(guild_id)
    if guild_lang:
        return guild_lang.lower()
    return 'en'

async def setup(bot: discord.Client):
    @bot.tree.command(name="guild-config", description="Configure server settings")
    @app_commands.describe(
        langue="Language for the server",
        announce_channel="Channel for bot announcements",
        allow_images="Allow images in chat",
        allow_user_preprompt="Allow user pre-prompts",
        allow_audios="Allow audio messages",
        guild_system_prompt="Custom system prompt for the server",
        allowed_channels="Channels where the bot is allowed to interact",
        allowed_roles="Roles that are allowed to interact with the bot",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.choices(langue=LANG_CHOICES)
    @app_commands.choices(allowed_channels=ALLOWED_CHANNELS)
    @app_commands.choices(allowed_roles=ALLOWED_ROLES)
    async def guild_config(
        interaction: discord.Interaction,
        langue: Optional[app_commands.Choice[str]] = None,
        announce_channel: Optional[discord.TextChannel] = None,
        allow_images: Optional[bool] = None,
        allow_user_preprompt: Optional[bool] = None,
        allow_audios: Optional[bool] = None,
        guild_system_prompt: Optional[str] = None,
        allowed_channels: Optional[app_commands.Choice[str]] = None,
        allowed_roles: Optional[app_commands.Choice[str]] = None
    ):
        logger.info(f"Commande /guild-config executed by {interaction.user.display_name}")
        logger.debug(f"Guild config parameters - langue: {langue}, announce_channel: {announce_channel}, allow_images: {allow_images}, allow_user_preprompt: {allow_user_preprompt}, allow_audios: {allow_audios}, guild_system_prompt: {guild_system_prompt}, allowed_channels: {allowed_channels}, allowed_roles: {allowed_roles}")
        await interaction.response.defer()

        lang_code = get_guild_lang_code(interaction.guild.id)

        update_data = {"id_discord": interaction.guild.id}
        summary = []

        if langue is not None:
            logger.debug(f"Processing language setting: {langue.value}")
            update_data["lang"] = langue.value
            summary.append(language_manager.get_translation(lang_code, "guild_config", "language_field", language_name=langue.name))

        if announce_channel is not None:
            logger.debug(f"Processing announcement channel: {announce_channel.id}")
            update_data["announce_channel"] = announce_channel.id
            summary.append(language_manager.get_translation(lang_code, "guild_config", "announce_channel_field", channel_mention=announce_channel.mention))

        if allow_images is not None:
            logger.debug(f"Processing allow_images setting: {allow_images}")
            update_data["allow_images"] = allow_images
            status = language_manager.get_translation(lang_code, "guild_config", "enabled_status") if allow_images else language_manager.get_translation(lang_code, "guild_config", "disabled_status")
            summary.append(language_manager.get_translation(lang_code, "guild_config", "allow_images_field", status=status))

        if allow_user_preprompt is not None:
            logger.debug(f"Processing allow_user_preprompt setting: {allow_user_preprompt}")
            update_data["allow_user_preprompt"] = allow_user_preprompt
            status = language_manager.get_translation(lang_code, "guild_config", "enabled_status") if allow_user_preprompt else language_manager.get_translation(lang_code, "guild_config", "disabled_status")
            summary.append(language_manager.get_translation(lang_code, "guild_config", "allow_user_preprompt_field", status=status))

        if allow_audios is not None:
            logger.debug(f"Processing allow_audios setting: {allow_audios}")
            update_data["allow_audios"] = allow_audios
            status = language_manager.get_translation(lang_code, "guild_config", "enabled_status") if allow_audios else language_manager.get_translation(lang_code, "guild_config", "disabled_status")
            summary.append(language_manager.get_translation(lang_code, "guild_config", "allow_audios_field", status=status))

        if guild_system_prompt is not None:
            logger.debug(f"Processing guild system prompt: {len(guild_system_prompt)} characters")
            update_data["guild_system_prompt"] = guild_system_prompt
            summary.append(language_manager.get_translation(lang_code, "guild_config", "guild_system_prompt_field", prompt=guild_system_prompt))

        if allowed_channels is not None:
            logger.debug(f"Processing allowed_channels setting: {allowed_channels.value}")
            if allowed_channels.value == "every":
                update_data["forbidden_channels"] = None
                summary.append(language_manager.get_translation(lang_code, "guild_config", "allowed_channels_every"))
            else:
                logger.debug("Initiating channel selection view")
                logger.info(f"Custom allowed channels selected by {interaction.user.display_name}")
                view = ChannelSelectView(interaction.guild)
                await interaction.followup.send(language_manager.get_translation(lang_code, "guild_config", "channel_select_prompt"), view=view, ephemeral=True)
                logger.debug("Waiting for user channel selection...")
                await view.wait()
                logger.debug(f"User selected {len(view.selected_channels)} channels")
                selected_channels = view.selected_channels
                update_data["forbidden_channels"] = [c.id for c in interaction.guild.channels if c.type == discord.ChannelType.text and c not in selected_channels]
                summary.append(language_manager.get_translation(lang_code, "guild_config", "allowed_channels_selected", count=len(selected_channels)))

        if allowed_roles is not None:
            logger.debug(f"Processing allowed_roles setting: {allowed_roles.value}")
            if allowed_roles.value == "every":
                update_data["forbidden_roles"] = None
                summary.append(language_manager.get_translation(lang_code, "guild_config", "allowed_roles_every"))
            else:
                logger.debug("Initiating role selection view")
                logger.info(f"Custom allowed roles selected by {interaction.user.display_name}")
                view = RoleSelectView(interaction.guild)
                await interaction.followup.send(language_manager.get_translation(lang_code, "guild_config", "role_select_prompt"), view=view, ephemeral=True)
                logger.debug("Waiting for user role selection...")
                await view.wait()
                logger.debug(f"User selected {len(view.selected_roles)} roles")
                selected_roles = view.selected_roles
                update_data["forbidden_roles"] = [r.id for r in interaction.guild.roles if r not in selected_roles]
                summary.append(language_manager.get_translation(lang_code, "guild_config", "allowed_roles_selected", count=len(selected_roles)))

        logger.debug(f"Final update data prepared: {len(update_data)} fields to update")

        if len(update_data) == 1:
            logger.debug("No parameters provided, aborting update")
            await interaction.followup.send(language_manager.get_translation(lang_code, "guild_config", "no_parameter"), ephemeral=True)
            return
        
        try:
            logger.debug(f"Attempting database update for guild {interaction.guild.name} ({interaction.guild.id})")
            update_data["settings_update"] = datetime.now().isoformat()
            supabase.table("server_settings").upsert(update_data).execute()
            logger.debug("Database update successful")

            summary_text = "\n".join(summary)
            if not summary_text:
                summary_text = language_manager.get_translation(lang_code, "guild_config", "no_changes")

            embed = discord.Embed(
                title=language_manager.get_translation(lang_code, "guild_config", "config_updated_title"),
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
            await interaction.followup.send(language_manager.get_translation(lang_code, "guild_config", "error_updating"), ephemeral=True)
