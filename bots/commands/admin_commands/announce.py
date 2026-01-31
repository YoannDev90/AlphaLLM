import logging
import os
from datetime import datetime

import discord
from discord import app_commands

from config import LOGGER_NAME
from utils.database.server_conf import get_server_setting
from utils.discord_utils.commands_ids import command_id_manager

logger = logging.getLogger(LOGGER_NAME)


class AnnounceModal(discord.ui.Modal, title="Send Announcement"):
    """Modal for entering announcement message"""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.message = discord.ui.TextInput(
            label="Announcement Message",
            style=discord.TextStyle.paragraph,
            placeholder="Type your announcement here (English, multi-line possible)",
            required=True,
            max_length=2000
        )
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        logger.info(f"Announcement modal submitted by {interaction.user} (ID: {interaction.user.id})")
        message = self.message.value

        # Create confirmation embed
        embed = discord.Embed(
            title="📢 Announcement Confirmation",
            description=f"**Message:**\n{message[:1000]}{'...' if len(message) > 1000 else ''}",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="📊 Statistics",
            value=f"• **Target Servers:** {len(self.bot.guilds)}\n"
                  f"• **Message Length:** {len(message)} characters",
            inline=False
        )
        embed.set_footer(text="⚠️ Please confirm sending this announcement")

        # Create confirmation view
        view = AnnounceConfirmView(message, self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class AnnounceConfirmView(discord.ui.View):
    """View for confirming announcement sending"""

    def __init__(self, message: str, bot):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.message = message
        self.bot = bot

    @discord.ui.button(label="✅ Send Announcement", style=discord.ButtonStyle.green)
    async def confirm_send(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)

        # Send announcement
        announced_guilds, failed_guilds = await send_announcement_to_guilds(self.bot, self.message)

        # Send final report
        embed = discord.Embed(
            title="✅ Announcement Complete",
            description="The announcement has been sent to all servers.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="📊 Results",
            value=f"• **Successful:** {announced_guilds} servers\n"
                  f"• **Failed:** {failed_guilds} servers\n"
                  f"• **Total:** {len(self.bot.guilds)} servers",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel_send(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Announcement Cancelled",
            description="The announcement has been cancelled.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await interaction.response.edit_message(embed=embed, view=None)


async def get_announce_channel(guild_id: int) -> int:
    """Get the configured announcement channel for a guild"""
    try:
        setting = await get_server_setting(guild_id, "announce_channel")
        if setting and isinstance(setting, int):
            return setting
    except Exception as e:
        logger.warning(f"Could not get announce channel for guild {guild_id}: {e}")
    return None


async def find_announcement_channel(guild):
    """Find the appropriate channel for announcements"""
    announce_channel_id = await get_announce_channel(guild.id)
    target_channel = None
    ask_define = False

    if announce_channel_id:
        target_channel = guild.get_channel(announce_channel_id)
        logger.info(f"Configured announcement channel found: {target_channel} (ID: {announce_channel_id})")
        ask_define = False

    if not target_channel and guild.system_channel:
        perms = guild.system_channel.permissions_for(guild.me)
        if perms.read_messages and perms.send_messages:
            target_channel = guild.system_channel
            logger.info(f"Using system channel: {target_channel}")
            ask_define = True

    if not target_channel:
        for channel in guild.text_channels:
            perms = channel.permissions_for(guild.me)
            if perms.read_messages and perms.send_messages:
                target_channel = channel
                logger.info(f"Using first accessible channel: {target_channel}")
                ask_define = True
                break

    return target_channel, ask_define


async def send_announcement_to_guilds(bot, message: str) -> tuple[int, int]:
    """Send announcement to all guilds"""
    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.set_footer(text="AlphaLLM Announcement")

    announced_guilds = 0
    failed_guilds = 0

    logger.info("Starting announcement to all servers")

    for guild in bot.guilds:
        logger.info(f"Processing server: {guild.name} (ID: {guild.id})")

        try:
            target_channel, ask_define = await find_announcement_channel(guild)

            if not target_channel:
                logger.warning(f"No announcement channel found for server {guild.name} (ID: {guild.id})")
                failed_guilds += 1
                continue

            await target_channel.send(embed=embed)
            logger.info(f"Announcement sent to {guild.name} in {target_channel.name}")
            announced_guilds += 1

            if ask_define:
                await send_channel_config_suggestion(target_channel, guild)

        except discord.Forbidden:
            logger.error(f"Insufficient permissions to send message to server {guild.name} (ID: {guild.id})")
            failed_guilds += 1
        except Exception as e:
            logger.error(f"Error sending to {guild.name} (ID: {guild.id}): {e}")
            failed_guilds += 1

    logger.info(f"Announcement complete: {announced_guilds} successful, {failed_guilds} failed")

    return announced_guilds, failed_guilds


async def send_channel_config_suggestion(target_channel, guild):
    """Send suggestion to configure announcement channel"""
    logger.info(f"Requesting announcement channel configuration for {guild.name} (ID: {guild.id})")
    try:
        mention = command_id_manager.get_command_mention('guild-config')
        await target_channel.send(
            f"<@{guild.owner_id}> Please configure this channel as the announcement channel using {mention} or use {target_channel.mention} by default."
        )
    except Exception as e:
        logger.error(f"Could not send config suggestion: {e}")


async def setup(bot: discord.Client):
    @bot.tree.command(name="announce", description="Send an announcement to all servers")
    async def announce(interaction: discord.Interaction):
        # Check if user is admin/owner
        if not interaction.user.guild_permissions.administrator and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        modal = AnnounceModal(bot)
        await interaction.response.send_modal(modal)
