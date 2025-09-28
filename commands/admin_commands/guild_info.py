import discord
import logging
from utils.config import logger_name
import os
from dotenv import load_dotenv
from bots.bot import bot as main_bot

load_dotenv()

logger = logging.getLogger(logger_name)
OWNER_ID = int(os.getenv('DEV_ID'))

async def setup(bot: discord.Client):
    @bot.tree.command(name="guild-info", description="Affiche les informations d'un serveur")
    async def guild_info(
        interaction: discord.Interaction, 
        guild_id: str = None):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /guild-info exécutée par {interaction.user.display_name} pour le serveur {guild_id or 'courant'}")

        if interaction.user.id != OWNER_ID:
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        if guild_id is None or guild_id.strip() == "":
            guild = interaction.guild
            if guild is None:
                await interaction.followup.send("Impossible de récupérer les informations du serveur courant.", ephemeral=True)
                return
        else:
            if not guild_id.isdigit() or int(guild_id) <= 0:
                await interaction.followup.send("L'ID du serveur fourni est invalide.", ephemeral=True)
                return
            guild = main_bot.get_guild(int(guild_id))
            if guild is None:
                await interaction.followup.send("Le bot n'est pas présent dans ce serveur ou l'ID est incorrect.", ephemeral=True)
                return

        try:
            embed = discord.Embed(
                title=f"📊 Informations du serveur {guild.name}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            
            embed.add_field(
                name="🏷️ Nom",
                value=guild.name,
                inline=True
            )
            
            embed.add_field(
                name="🆔 ID",
                value=f"`{guild.id}`",
                inline=True
            )
            
            embed.add_field(
                name="👑 Propriétaire",
                value=f"{guild.owner.mention} ({guild.owner.name})" if guild.owner else "Inconnu",
                inline=True
            )
            
            embed.add_field(
                name="👥 Membres",
                value=f"**{guild.member_count}** membres",
                inline=True
            )
            
            embed.add_field(
                name="📅 Créé le",
                value=guild.created_at.strftime("%d/%m/%Y à %H:%M"),
                inline=True
            )
            
            if guild.me:
                embed.add_field(
                    name="🤖 Bot rejoint le",
                    value=guild.me.joined_at.strftime("%d/%m/%Y à %H:%M"),
                    inline=True
                )
            
            embed.add_field(
                name="🌍 Région",
                value=str(guild.preferred_locale) if guild.preferred_locale else "Inconnue",
                inline=True
            )
            
            embed.add_field(
                name="🔒 Niveau de vérification",
                value=str(guild.verification_level).title(),
                inline=True
            )
            
            embed.add_field(
                name="📢 Canaux",
                value=f"**{len(guild.channels)}** canaux",
                inline=True
            )
            
            embed.add_field(
                name="🎭 Rôles",
                value=f"**{len(guild.roles)}** rôles",
                inline=True
            )
            
            embed.set_footer(
                text=f"Demandé par {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )

            await interaction.followup.send(embed=embed)
        except discord.HTTPException as e:
            logger.error(f"Erreur HTTP lors de l'exécution de la commande guild-info pour {guild.id}: {e}")
            await interaction.followup.send("Erreur lors de la récupération des données. Veuillez réessayer plus tard.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'exécution de la commande guild-info pour {guild.id}: {e}")
            await interaction.followup.send("Erreur inattendue. Veuillez réessayer plus tard.", ephemeral=True)