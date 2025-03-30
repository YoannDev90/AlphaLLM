import discord
import logging
from utils.langs import get_translation

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="help", description="Affiche la liste des commandes disponibles")
    async def help_command(interaction: discord.Interaction):
        logger.info(f"Commande help exécutée par {interaction.user.display_name}")

        embed = discord.Embed(
            color=discord.Color.default(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        categories = {
            "\n🔍 Général": [
                "‎",
                "Affiche la latence du bot \n ```/ping```",
                "Affiche la liste des commandes disponibles \n ```/help```",
                "Envoie un message au développeur \n ```/contact```",
            ],
            "\n🖼️ Images": [
                "‎",
                "Génère une image basée sur le prompt donné \n ```/image```",
                "Génère plusieurs images basées sur le prompt donné \n ```/multimage```",
            ],
            "\n📊 Statistiques et Liens": [
                "‎",
                "Affiche le lien du serveur de support \n ```/support```",
                "Affiche le lien de vote du bot \n ```/vote```",
                "Affiche le lien d'invitation du bot \n ```/invite```",
            ],
        }

        for category, commands in categories.items():
            field_value = "\n".join(commands)
            embed.add_field(name=f"**{category}**", value=field_value, inline=False)

        await interaction.response.send_message(embed=embed)
