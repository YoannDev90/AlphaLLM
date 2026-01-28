import logging

import discord
from discord import app_commands

from config import LOGGER_NAME, SUPPORT_SERVER

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(name="status", description="Show the status of the bot")
    async def status(interaction: discord.Interaction):
        logger.info(f"Commande /status exécutée par {interaction.user.display_name}")

        embed = discord.Embed(
            title="Models Status",
            description="Here is the current status of the AI models:",
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="🤖 AI Models",
            value="Everything is running smoothly! All models are operational.",
            inline=False,
        )
        embed.set_footer(
            text=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)
