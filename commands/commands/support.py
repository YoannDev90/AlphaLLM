import discord
from discord import app_commands
import logging
from utils.config import logger_name, SUPPORT_SERVER

logger = logging.getLogger(logger_name)

async def setup(bot: discord.Client):
    @bot.tree.command(name="support", description="Show the support server link")
    async def support(interaction: discord.Interaction):
        link = SUPPORT_SERVER
        logger.info(f"Commande /support exécutée par {interaction.user.display_name}")

        embed = discord.Embed(
            title="Support Server Link",
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="Join support server",
            value=f"[Click here to join server]({link})",
            inline=False
        )
        embed.set_footer(text=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
