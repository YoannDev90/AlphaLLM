import logging
from typing import Optional

import discord
from discord import app_commands

from config import LOGGER_NAME
from utils.database.server_conf import (set_allowed_channels,
                                        set_allowed_roles,
                                        set_announcement_channel, set_language)
from utils.views.channels import ChannelSelectView
from utils.views.roles import RoleSelectView

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
        allowed_channels: Optional[app_commands.Choice[str]] = None,
        allowed_roles: Optional[app_commands.Choice[str]] = None,
    ):
        logger.info(
            f"Commande /guild-config executed by {interaction.user.display_name}"
        )
        await interaction.response.defer()

        if langue is not None:
            await set_language(interaction.guild.id, langue.value)

        if announce_channel is not None:
            await set_announcement_channel(interaction.guild.id, announce_channel.id)

        if allowed_channels is not None:
            if allowed_channels.value == "every":
                allowed = [
                    c.id
                    for c in interaction.guild.channels
                    if c.type == discord.ChannelType.text
                ]
            else:
                view = ChannelSelectView(interaction.guild)
                await interaction.followup.send(
                    "Select allowed channels:", view=view, ephemeral=True
                )
                await view.wait()
                selected_channels = view.selected_channels
                allowed = [
                    c.id
                    for c in interaction.guild.channels
                    if c.type == discord.ChannelType.text and c in selected_channels
                ]
            await set_allowed_channels(interaction.guild.id, allowed)

        if allowed_roles is not None:
            if allowed_roles.value == "every":
                allowed = [r.id for r in interaction.guild.roles]
            else:
                view = RoleSelectView(interaction.guild)
                await interaction.followup.send(
                    "Select allowed roles:", view=view, ephemeral=True
                )
                await view.wait()
                selected_roles = view.selected_roles
                allowed = [r.id for r in interaction.guild.roles if r in selected_roles]
            await set_allowed_roles(interaction.guild.id, allowed)

        await interaction.followup.send("Configuration updated.", ephemeral=True)
