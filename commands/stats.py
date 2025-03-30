"""
stats.py

This module defines the `/stats` command, which sends some statistics.
"""

import discord
from discord import app_commands
from utils.langs import get_translation
import logging

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    """
    Sets up the `/stats` command for the bot.

    Args:
        bot (discord.Client): The Discord bot instance.
    """
    @bot.tree.command(name="stats", description="Montre les statistiques du bot")
    async def stats(interaction: discord.Interaction):
        
        logger.info(f"Commande stats exécutée par {interaction.user.display_name}")

        embed = discord.Embed(
            title="Statistiques du bot",
            description="Voici quelques statistiques sur le bot :",
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Nombre de serveurs", value=len(bot.guilds), inline=False)
        embed.add_field(name="Nombre d'utilisateurs", value=len(set(bot.get_all_members())), inline=False)
        embed.add_field(name="Version du bot", value="4.2.0", inline=False)
        embed.add_field(name="Langues", value="Français, Anglais", inline=False)
        embed.add_field(name="Propriétaire", value="<@1123534156626939945>", inline=False)
        embed.add_field(name="Support", value="[Rejoindre le serveur](https://discord.gg/QGvyrUgwdK)", inline=False)
        embed.add_field(name="Vote", value="[Voter pour le bot](https://top.gg/bot/123456789012345678/vote)", inline=False)
        embed.add_field(name="Invite", value="[Inviter le bot](https://discord.com/oauth2/authorize?client_id=123456789012345678&scope=bot&permissions=8)", inline=False)
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
