import discord
import logging
from utils.langs import get_language, get_translation as tlt

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="ping", description="Affiche la latence du bot")
    async def ping(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        logger.info(f"Commande ping exécutée par {interaction.user.display_name}")
        
        user_lang = get_language(interaction.user.id)

        latence = round(bot.latency * 1000)

        text = (
            tlt(language=user_lang, key="current_latency", latency=latence)
        )

        embed = discord.Embed(
            title=text,
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=tlt(language=user_lang, key="embed_footer", user=interaction.user.display_name), icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)
