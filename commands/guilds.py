import discord
from discord import app_commands
import logging
from dotenv import load_dotenv
from utils.langs import get_translation
import os

load_dotenv()
discord_logo = "https://img.icons8.com/?size=100&id=M725CLW4L7wE&format=png&color=000000"

logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="guilds", description="Affiche la liste des serveurs où le bot est présent")
    async def guilds(interaction: discord.Interaction):
        try:
            if not str(interaction.user.id) == os.getenv("DEV_ID"):
                await interaction.response.send_message("Vous n'avez pas la permission d'exécuter cette commande administrateur.", ephemeral=True)
                return

            guilds = bot.guilds
            logger.info(f"Commande guilds exécutée par {interaction.user.display_name}")
            await interaction.response.defer()
            await interaction.followup.send("Récupération des informations en cours...")

            # Trier les serveurs par date d'ajout
            sorted_guilds = sorted(guilds, key=lambda guild: guild.me.joined_at if guild.me else discord.utils.utcnow())

            for guild in sorted_guilds:
                description = f"ID : `{guild.id}`\n"
                description += f"Propriétaire : <@{guild.owner.id}>\n"
                description += f"Date d'ajout du bot : {guild.me.joined_at.strftime('%d/%m/%Y %H:%M:%S') if guild.me else 'Inconnue'}\n"
                description += f"Nombre de membres : {guild.member_count}\n"
                description += f"Nombre de modèles activés : None\n"
                description += f"Nombre d'images générées : Nonde\n"
                description += f"Nombre de commandes exécutées : None\n"
                description += f"Nombre de questions posées au bot : None\n"
                embed = discord.Embed(
                    title=f"Serveur : {guild.name}",
                    description=description,
                    color=discord.Color.default(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_thumbnail(url=guild.icon.url if guild.icon else discord_logo)
                embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

                await interaction.channel.send(embed=embed)

        except discord.HTTPException as e:
            logger.error(f"Erreur HTTP lors de l'exécution de la commande guilds: {e}")
            await interaction.response.send_message("Erreur lors de la récupération des données. Veuillez réessayer plus tard.", ephemeral=True)

        except discord.Forbidden as e:
            logger.error(f"Erreur Forbidden lors de l'exécution de la commande guilds: {e}")
            await interaction.response.send_message("Le bot n'a pas la permission de récupérer les informations demandées.", ephemeral=True)

        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'exécution de la commande guilds: {e}")
            await interaction.response.send_message("Erreur inattendue. Veuillez réessayer plus tard.", ephemeral=True)
