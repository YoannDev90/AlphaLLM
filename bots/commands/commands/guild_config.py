import discord
from discord import app_commands
from typing import Dict, Optional
from datetime import datetime
import logging
import json

from utils.views.channels import ChannelSelectView
from utils.views.roles import RoleSelectView
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

LANG_CHOICES = [
    app_commands.Choice(name="Français 🇫🇷", value="FR"),
    app_commands.Choice(name="English 🇬🇧", value="EN"),
    app_commands.Choice(name="Español 🇪🇸", value="ES"),
    app_commands.Choice(name="Deutsch 🇩🇪", value="DE"),
]

ALLOWED_CHANNELS = [
    app_commands.Choice(name="Allow every channel", value="every"),
    app_commands.Choice(name="Allow specific channels", value="specific"),
]

ALLOWED_ROLES = [
    app_commands.Choice(name="Allow every role, including @everyone", value="every"),
    app_commands.Choice(name="Allow specific roles", value="specific"),
]

async def setup(bot: discord.Client):
    @bot.tree.command(name="guild-config", description="Configure server settings")
    @app_commands.describe(
        langue="Language for the server",
        announce_channel="Channel for bot announcements",
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
        guild_system_prompt: Optional[str] = None,
        allowed_channels: Optional[app_commands.Choice[str]] = None,
        allowed_roles: Optional[app_commands.Choice[str]] = None
    ):
        logger.info(f"Commande /guild-config executed by {interaction.user.display_name}")
        await interaction.response.defer()

        update_data = {"id_discord": interaction.guild.id}

        if langue is not None:
            update_data["lang"] = langue.value

        if announce_channel is not None:
            update_data["announce_channel"] = announce_channel.id

        if guild_system_prompt is not None:
            update_data["guild_system_prompt"] = guild_system_prompt

        if allowed_channels is not None:
            if allowed_channels.value == "every":
                update_data["forbidden_channels"] = None
            else:
                view = ChannelSelectView(interaction.guild)
                await interaction.followup.send("Sélectionnez les salons autorisés :", view=view, ephemeral=True)
                await view.wait()
                selected_channels = view.selected_channels
                update_data["forbidden_channels"] = [c.id for c in interaction.guild.channels if c.type == discord.ChannelType.text and c not in selected_channels]

        if allowed_roles is not None:
            if allowed_roles.value == "every":
                update_data["forbidden_roles"] = None
            else:
                view = RoleSelectView(interaction.guild)
                await interaction.followup.send("Sélectionnez les rôles autorisés :", view=view, ephemeral=True)
                await view.wait()
                selected_roles = view.selected_roles
                update_data["forbidden_roles"] = [r.id for r in interaction.guild.roles if r not in selected_roles]

        if len(update_data) == 1:
            await interaction.followup.send("Aucun paramètre fourni.", ephemeral=True)
            return

        update_data["settings_update"] = datetime.now().isoformat()

        json_output = json.dumps(update_data, indent=4)
        await interaction.followup.send(f"```json\n{json_output}\n```", ephemeral=True)
        logger.info(f"Guild config JSON: {update_data}")
