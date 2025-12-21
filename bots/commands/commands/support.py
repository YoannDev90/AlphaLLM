import logging

import discord
from discord import app_commands

from config import LOGGER_NAME, SUPPORT_SERVER

logger = logging.getLogger(LOGGER_NAME)

async def setup(bot: discord.Client):
    @bot.tree.command(name="support", description="Show the support server link")
    async def support(interaction: discord.Interaction):
        logger.info(f"Commande /support exécutée par {interaction.user.display_name}")

        embed = discord.Embed(
            title="Support Server Link",
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="Join support server",
            value=f"[Click here to join server]({SUPPORT_SERVER})",
            inline=False
        )
        embed.set_footer(text=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
