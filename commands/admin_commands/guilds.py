import discord
import logging
from dotenv import load_dotenv
import os

load_dotenv()

OWNER_ID = int(os.getenv('DEV_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))
logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="guilds", description="Affiche la liste des serveurs où le bot est présent")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def guilds(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /guilds exécutée par {interaction.user.display_name}")

        if interaction.user.id != OWNER_ID:
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        try:
            guilds = bot.guilds
            sorted_guilds = sorted(
                guilds,
                key=lambda guild: guild.me.joined_at if guild.me else discord.utils.utcnow()
            )

            embeds = []
            for guild in sorted_guilds:
                description = (
                    f"ID : `{guild.id}`\n"
                    f"Propriétaire : <@{guild.owner_id}>\n"
                    f"Date d'ajout du bot : {guild.me.joined_at.strftime('%d/%m/%Y %H:%M:%S') if guild.me and guild.me.joined_at else 'Inconnue'}\n"
                    f"Nombre de membres : {guild.member_count}\n"
                )
                embed = discord.Embed(
                    title=f"Serveur : {guild.name}",
                    description=description,
                    color=discord.Color.default(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_thumbnail(url=guild.icon.url if guild.icon else "https://img.icons8.com/ios-filled/500/discord-logo.png")
                embed.set_footer(text=f"Demandé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
                embeds.append(embed)

            for i in range(0, len(embeds), 10):
                await interaction.followup.send(embeds=embeds[i:i+10], ephemeral=True)

        except discord.HTTPException as e:
            logger.error(f"Erreur HTTP lors de l'exécution de la commande guilds: {e}")
            await interaction.followup.send("Erreur lors de la récupération des données. Veuillez réessayer plus tard.", ephemeral=True)
        except discord.Forbidden as e:
            logger.error(f"Erreur Forbidden lors de l'exécution de la commande guilds: {e}")
            await interaction.followup.send("Le bot n'a pas la permission de récupérer les informations demandées.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'exécution de la commande guilds: {e}")
            await interaction.followup.send("Erreur inattendue. Veuillez réessayer plus tard.", ephemeral=True)
