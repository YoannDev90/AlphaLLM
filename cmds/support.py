import logging

import discord
from discord import app_commands

from core.config import cfg
from utils.logger import get_logger

logger = get_logger()


async def setup(tree: app_commands.CommandTree, bot: discord.Client):
    @tree.command(name="support", description="Show the support server link")
    async def support_command(interaction: discord.Interaction):
        logger.info(f"Command /support executed by {interaction.user.display_name}")

        embed = discord.Embed(
            title="Support Server Link",
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="Join support server",
            value=f"[Click here to join server]({cfg.LINKS['support_server']})",
            inline=False,
        )
        embed.set_footer(
            text=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)
