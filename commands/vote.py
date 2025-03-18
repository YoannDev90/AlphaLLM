import discord
from discord import app_commands
from utils.langs import get_translation
import logging

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="vote", description="Envoie le lien Top.gg")
    async def vote(interaction: discord.Interaction):
        link = "https://top.gg/bot/1286951908786962442#reviews"
        logger.info(f"Commande vote exécutée par {interaction.user.display_name}")

        embed = discord.Embed(
                title="Lien du vote sur **Top.gg**",
                color=discord.Color.default(),
                timestamp=discord.utils.utcnow()
            )
        embed.add_field(
            name="Merci de voter pour le bot !",
            value=f"[AlphaLLM]({link})",
            inline=False
        )
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)        
        await interaction.response.send_message(embed=embed)
