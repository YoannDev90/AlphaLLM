import discord
import logging
from utils.config import logger_name
from dotenv import load_dotenv
import os
from bots.bot import bot as main_bot

load_dotenv()

OWNER_ID = int(os.getenv('DEV_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))
logger = logging.getLogger(logger_name)

async def setup(bot: discord.Client):
    @bot.tree.command(name="guilds", description="Affiche la liste des serveurs où le bot est présent")
    async def guilds(interaction: discord.Interaction):
        logger.info(f"Commande /guilds exécutée par {interaction.user.display_name}")

        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return
        
        bot = main_bot
        
        if bot.guilds is None:
            await interaction.response.send_message("Le bot n'est pas présent dans d'autres serveurs.", ephemeral=True)
            return

        try:
            guilds = bot.guilds
            sorted_guilds = sorted(
                guilds,
                key=lambda guild: guild.me.joined_at if guild.me else discord.utils.utcnow()
            )

            total_guilds = len(sorted_guilds)
            total_members = sum(guild.member_count for guild in guilds if guild.member_count)
            
            # Premier message : Statistiques générales via interaction.response
            stats_embed = discord.Embed(
                title="📊 Statistiques des serveurs",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            stats_embed.add_field(
                name="🏢 Serveurs",
                value=f"**{total_guilds}** serveurs",
                inline=True
            )
            
            stats_embed.add_field(
                name="👥 Membres",
                value=f"**{total_members:,}** membres",
                inline=True
            )
            
            stats_embed.add_field(
                name="📈 Moyenne",
                value=f"**{total_members // total_guilds if total_guilds > 0 else 0}** membres/serveur",
                inline=True
            )
            
            stats_embed.set_footer(
                text=f"Demandé par {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )

            await interaction.response.send_message(embed=stats_embed, ephemeral=True)
            
            # Deuxième message : Liste détaillée via channel.send (par groupes de 10)
            servers_per_message = 10
            total_messages = (total_guilds + servers_per_message - 1) // servers_per_message
            
            for message_num in range(total_messages):
                start_idx = message_num * servers_per_message
                end_idx = min(start_idx + servers_per_message, total_guilds)
                page_guilds = sorted_guilds[start_idx:end_idx]
                
                details_embed = discord.Embed(
                    title=f"📋 Liste des serveurs ({message_num + 1}/{total_messages})",
                    description=f"Serveurs {start_idx + 1} à {end_idx} sur {total_guilds}",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )

                # Liste des serveurs pour ce message
                guild_list = []
                for i, guild in enumerate(page_guilds, start=start_idx + 1):
                    joined_date = guild.me.joined_at.strftime('%d/%m/%Y') if guild.me and guild.me.joined_at else 'Inconnue'
                    guild_info = f"`{i}.` **{guild.name}**\n└ ID: `{guild.id}` • 👥 {guild.member_count} • 📅 {joined_date}"
                    guild_list.append(guild_info)

                details_embed.add_field(
                    name="🏢 Serveurs",
                    value="\n\n".join(guild_list),
                    inline=False
                )

                details_embed.set_footer(
                    text=f"Demandé par {interaction.user.display_name} • Page {message_num + 1}/{total_messages}",
                    icon_url=interaction.user.display_avatar.url
                )

                # Envoyer dans le canal via channel.send
                await interaction.channel.send(embed=details_embed)

        except discord.HTTPException as e:
            logger.error(f"Erreur HTTP lors de l'exécution de la commande guilds: {e}")
            await interaction.response.send_message("Erreur lors de la récupération des données. Veuillez réessayer plus tard.", ephemeral=True)
        except discord.Forbidden as e:
            logger.error(f"Erreur Forbidden lors de l'exécution de la commande guilds: {e}")
            await interaction.response.send_message("Le bot n'a pas la permission de récupérer les informations demandées.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'exécution de la commande guilds: {e}")
            await interaction.response.send_message("Erreur inattendue. Veuillez réessayer plus tard.", ephemeral=True)
