import discord

from bots.bot import bot as main_bot
from utils.config import LOGGER_NAME, is_dev_id
from utils.core.logger import get_logger

logger = get_logger(LOGGER_NAME)

CHOICES = [
    discord.app_commands.Choice(name="stats", value=0),
    discord.app_commands.Choice(name="latest", value=1),
    discord.app_commands.Choice(name="all", value=2),
]

async def setup(bot: discord.Client):
    @bot.tree.command(name="guilds", description="Affiche la liste des serveurs où le bot est présent")
    @discord.app_commands.choices(data=CHOICES)
    async def guilds(interaction: discord.Interaction, data: discord.app_commands.Choice[int]):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /guilds [{data.name}] exécutée par {interaction.user.display_name}")

        if not is_dev_id(interaction.user.id):
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return
        
        bot = main_bot
        
        if bot.guilds is None:
            await interaction.followup.send("Le bot n'est pas présent dans d'autres serveurs.", ephemeral=True)
            return

        try:
            guilds = bot.guilds
            sorted_guilds = sorted(
                guilds,
                key=lambda guild: guild.me.joined_at if guild.me else discord.utils.utcnow(),
                reverse=True
            )

            total_guilds = len(sorted_guilds)
            total_members = sum(guild.member_count for guild in guilds if guild.member_count)
            
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

            match data.value:
                case 0:
                    await interaction.followup.send(embed=stats_embed)
                case 1:
                    latest_guilds = sorted_guilds[:5]
                    
                    details_embed = discord.Embed(
                        title="📋 5 derniers serveurs rejoints",
                        description=f"Serveurs 1 à {len(latest_guilds)} sur {total_guilds}",
                        color=discord.Color.blue(),
                        timestamp=discord.utils.utcnow()
                    )

                    guild_list = []
                    for i, guild in enumerate(latest_guilds, start=1):
                        joined_date = guild.me.joined_at.strftime('%d/%m/%Y') if guild.me and guild.me.joined_at else 'Inconnue'
                        guild_info = f"`{i}.` **{guild.name}**\n ID: `{guild.id}` • 👥 {guild.member_count} • 📅 {joined_date}"
                        guild_list.append(guild_info)

                    details_embed.add_field(
                        name="🏢 5 derniers serveurs",
                        value="\n\n".join(guild_list),
                        inline=False
                    )

                    details_embed.set_footer(
                        text=f"Demandé par {interaction.user.display_name}",
                        icon_url=interaction.user.display_avatar.url
                    )

                    await interaction.channel.send(embed=details_embed)
                case 2:                 
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

                        await interaction.channel.send(embed=details_embed)

        except discord.HTTPException as e:
            logger.error(f"Erreur HTTP lors de l'exécution de la commande guilds: {e}")
            await interaction.followup.send("Erreur lors de la récupération des données. Veuillez réessayer plus tard.", ephemeral=True)
        except discord.Forbidden as e:
            logger.error(f"Erreur Forbidden lors de l'exécution de la commande guilds: {e}")
            await interaction.followup.send("Le bot n'a pas la permission de récupérer les informations demandées.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'exécution de la commande guilds: {e}")
            await interaction.followup.send("Erreur inattendue. Veuillez réessayer plus tard.", ephemeral=True)
