import discord
from discord import app_commands
import logging
from utils.langs import get_translation

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="invite", description="Envoie le lien d'invitation du bot")
    async def invite(interaction: discord.Interaction):
        link = "https://discord.com/oauth2/authorize?client_id=1286951908786962442"
        logger.info(f"Commande invite exécutée par {interaction.user.display_name}")

        embed = discord.Embed(
                title="Lien d'invitation du bot **AlphaLLM**",
                color=discord.Color.default(),
                timestamp=discord.utils.utcnow()
            )
        embed.add_field(
            name="Invitez le bot sur votre serveur !",
            value=f"[AlphaLLM]({link})",
            inline=False
        )
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)        
        await interaction.response.send_message(embed=embed)
