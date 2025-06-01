import discord
from discord import app_commands
from utils.langs import get_language, get_translation as tlt
import logging

logger = logging.getLogger('AlphaLLM')

desc = """
Voici comment utiliser le bot :
💬 - Pour discuter, débattre, jouer, ... avec moi, mentionnez moi simplement dans vos messages ( <@1286951908786962442> ).
🖼️ - Pour générer des images, utilisez la commande `/image`.
📜 - Pour voir la liste des commandes disponibles, utilisez `/commands`.
🔗 - Pour discuter avec mon développeur ou demander de l'aide avec le bot, utilisez `/support`.
"""

async def setup(bot: discord.Client):
    @bot.tree.command(name="help", description="Show help informations")
    async def help(interaction: discord.Interaction):
        logger.info(f"Commande help exécutée par {interaction.user.display_name}")

        user_lang = get_language(interaction.user.id)

        embed = discord.Embed(
            title="Aide",
            description=desc,
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_footer(text=tlt(language=user_lang, key="embed_footer", user=interaction.user.display_name), icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
