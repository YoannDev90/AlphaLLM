import asyncio
from datetime import datetime, timedelta, timezone
from typing import List

import discord
from discord import app_commands

from cmds._shared import is_user_authorized
from core.config import cfg
from utils.logger import get_logger

logger = get_logger()


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
            max_length=2000,
        )
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        logger.info(
            f"Announcement modal submitted by {interaction.user} (ID: {interaction.user.id})"
        )
        message = self.message.value

        # Create confirmation embed
        embed = discord.Embed(
            title="📢 Announcement Confirmation",
            description=f"**Message:**\n{message[:1000]}{'...' if len(message) > 1000 else ''}",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="📊 Statistics",
            value=f"• **Target Servers:** {len(self.bot.guilds)}\n"
            f"• **Message Length:** {len(message)} characters",
            inline=False,
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
    async def confirm_send(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()

        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)

        # Send announcement
        announced_guilds, failed_guilds = await send_announcement_to_guilds(
            self.bot, self.message
        )

        # Send final report
        embed = discord.Embed(
            title="✅ Announcement Complete",
            description="The announcement has been sent to all servers.",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="📊 Results",
            value=f"• **Successful:** {announced_guilds} servers\n"
            f"• **Failed:** {failed_guilds} servers\n"
            f"• **Total:** {len(self.bot.guilds)} servers",
            inline=False,
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel_send(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="❌ Announcement Cancelled",
            description="The announcement has been cancelled.",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        await interaction.response.edit_message(embed=embed, view=None)


async def find_announcement_channel(guild):
    """Find the best channel for announcements using automated criteria.

    Priority order:
    1. Discord "Updates" / News channel (community servers feature)
    2. Most active text channel in the last 24 hours
    3. First accessible text channel (fallback)
    """

    # ── 1. Discord "Updates" / News channel (community servers) ──
    # News channels (type 5) are the official "Announcement Channels" on community servers.
    news_channels = [
        ch
        for ch in guild.channels
        if ch.type == discord.ChannelType.news
        and ch.permissions_for(guild.me).send_messages
    ]

    if news_channels:
        # Prefer channels with update-related keywords in the name
        update_keywords = [
            "update",
            "annonce",
            "announcement",
            "news",
            "changelog",
            "patch",
            "info",
        ]
        ranked = sorted(
            news_channels,
            key=lambda ch: any(kw in ch.name.lower() for kw in update_keywords),
            reverse=True,
        )
        target = ranked[0]
        logger.info(f"Found announcement/news channel: {target} (ID: {target.id})")
        return target

    # ── 2. Most active text channel in the last 24 hours ──
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    accessible_channels = [
        ch
        for ch in guild.text_channels
        if ch.permissions_for(guild.me).read_messages
        and ch.permissions_for(guild.me).send_messages
    ]

    best_channel = None
    best_count = -1

    for ch in accessible_channels:
        try:
            count = 0
            async for _ in ch.history(limit=100, after=cutoff):
                count += 1
            if count > best_count:
                best_count = count
                best_channel = ch
        except discord.Forbidden:
            continue
        except Exception as e:
            logger.debug(f"Could not read history for #{ch.name}: {e}")
            continue

    if best_channel and best_count > 0:
        logger.info(
            f"Most active channel in 24h: #{best_channel.name} "
            f"({best_count} messages) in {guild.name}"
        )
        return best_channel

    # ── 3. Fallback: first accessible text channel ──
    if accessible_channels:
        logger.info(
            f"Using first accessible channel: #{accessible_channels[0].name} in {guild.name}"
        )
        return accessible_channels[0]

    logger.warning(f"No suitable channel found for {guild.name} (ID: {guild.id})")
    return False


async def send_announcement_to_guilds(bot, message: str) -> tuple[int, int]:
    """Send announcement to all guilds concurrently using batches.

    Guilds are processed in parallel batches to respect Discord rate limits
    while maximising throughput. Between each batch a short pause lets the
    REST bucket refill.
    """
    BATCH_SIZE = 8
    BATCH_DELAY = 0.5  # seconds between batches

    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="AlphaLLM Announcement")

    announced = 0
    failed = 0
    guilds = list(bot.guilds)

    logger.info(
        f"Starting announcement to {len(guilds)} servers (batch size: {BATCH_SIZE})"
    )

    async def _send_to_guild(guild: discord.Guild) -> tuple[bool, str]:
        """Find channel & send embed for one guild. Returns (success, detail)."""
        try:
            target_channel = await find_announcement_channel(guild)

            if not target_channel:
                return False, f"No channel found for {guild.name}"

            await target_channel.send(embed=embed)
            return True, f"{guild.name} → #{target_channel.name}"

        except discord.Forbidden:
            return False, f"Forbidden on {guild.name}"
        except Exception as e:
            return False, f"Error on {guild.name}: {e}"

    # Process guilds in batches
    for i in range(0, len(guilds), BATCH_SIZE):
        batch = guilds[i : i + BATCH_SIZE]
        logger.info(
            f"Processing batch {i // BATCH_SIZE + 1} "
            f"({len(batch)} servers: {', '.join(g.name for g in batch)})"
        )

        results = await asyncio.gather(
            *(_send_to_guild(g) for g in batch), return_exceptions=True
        )

        for result in results:
            if isinstance(result, Exception):
                failed += 1
                logger.error(f"Unhandled exception: {result}")
            elif result[0]:
                announced += 1
                logger.info(f"✅ {result[1]}")
            else:
                failed += 1
                logger.warning(f"❌ {result[1]}")

        # Brief pause between batches to respect rate limits
        if i + BATCH_SIZE < len(guilds):
            await asyncio.sleep(BATCH_DELAY)

    logger.info(
        f"Announcement complete: {announced} successful, {failed} failed "
        f"(out of {len(guilds)} servers)"
    )
    return announced, failed


async def setup(tree: app_commands.CommandTree, bot: discord.Client):
    @tree.command(name="announce", description="Send an announcement to all servers")
    @app_commands.check(is_user_authorized)
    async def announce(interaction: discord.Interaction):
        modal = AnnounceModal(bot)
        await interaction.response.send_modal(modal)
