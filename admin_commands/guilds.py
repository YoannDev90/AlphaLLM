import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
from utils.langs import get_translation as tlt
import os

load_dotenv()

logger = logging.getLogger('AlphaLLM')

async def setup(bot: commands.Bot):
    @bot.command(name="guilds")
    @commands.is_owner()
    async def guilds(ctx):
        logger.info(f"Commande guilds exécutée par {ctx.author.display_name}")
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            logger.warning("Impossible de supprimer le message de commande. Vérifiez les permissions.")        
        guilds = bot.guilds
        sorted_guilds = sorted(guilds, key=lambda guild: guild.me.joined_at if guild.me else discord.utils.utcnow())

        for guild in sorted_guilds:
            description = f"ID : `{guild.id}`\n"
            description += f"Propriétaire : <@{guild.owner.id}>\n"
            description += f"Date d'ajout du bot : {guild.me.joined_at.strftime('%d/%m/%Y %H:%M:%S') if guild.me else 'Inconnue'}\n"
            description += f"Nombre de membres : {guild.member_count}\n"
            embed = discord.Embed(
                title=f"Serveur : {guild.name}",
                description=description,
                color=discord.Color.default(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else "https://img.icons8.com/ios-filled/500/discord-logo.png")
            embed.set_footer(text=f"Demandé par {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

            await ctx.send(embed=embed)

        # Gestion des erreurs
        try:
            pass  # Code principal
        except discord.HTTPException as e:
            logger.error(f"Erreur HTTP lors de l'exécution de la commande guilds: {e}")
            await ctx.send("Erreur lors de la récupération des données. Veuillez réessayer plus tard.")
        except discord.Forbidden as e:
            logger.error(f"Erreur Forbidden lors de l'exécution de la commande guilds: {e}")
            await ctx.send("Le bot n'a pas la permission de récupérer les informations demandées.")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'exécution de la commande guilds: {e}")
            await ctx.send("Erreur inattendue. Veuillez réessayer plus tard.")
