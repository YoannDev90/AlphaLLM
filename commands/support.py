import discord
from discord import app_commands
from utils.langs import get_language, get_translation as tlt
import logging

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="support", description="Envoie le lien du serveur Discord de support")
    async def support(interaction: discord.Interaction):
        link = "https://discord.gg/QGvyrUgwdK"
        logger.info(f"Commande support exécutée par {interaction.user.display_name}")

        user_lang = get_language(interaction.user.id)

        embed = discord.Embed(
            title=tlt(language=user_lang, key="support_server_link_embed"),
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name=tlt(language=user_lang, key="join_server"),
            value=f"[{tlt(language=user_lang, key='join_server_button')}]({link})",
            inline=False
        )
        embed.set_footer(text=tlt(language=user_lang, key="embed_footer", user=interaction.user.display_name), icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
