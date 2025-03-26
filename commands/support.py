"""
support.py

This module defines the `/support` command, which sends the link to the support Discord server.
"""

import discord
from discord import app_commands
from utils.langs import get_translation
import logging

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    """
    Sets up the `/support` command for the bot.

    Args:
        bot (discord.Client): The Discord bot instance.
    """
    @bot.tree.command(name="support", description="Envoie le lien du serveur Discord de support")
    async def support(interaction: discord.Interaction):
        """
        Sends the link to the support Discord server.

        Args:
            interaction (discord.Interaction): The interaction object for the command.
        """
        link = "https://discord.gg/QGvyrUgwdK"
        logger.info(f"Commande support exécutée par {interaction.user.display_name}")

        embed = discord.Embed(
            title="Lien du serveur **AlphaLLM - Support**",
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="Rejoignez le serveur Discord de support pour obtenir de l'aide !",
            value=f"[Rejoindre le serveur]({link})",
            inline=False
        )
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
