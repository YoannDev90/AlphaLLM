import logging

import discord

from bots.bot import bot as main_bot
from config import DEV_IDS, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(name="guild-info", description="Display server information")
    async def guild_info(interaction: discord.Interaction, guild_id: str = None):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message(
                "❌ You are not authorized to use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(
            f"Command /guild-info executed by {interaction.user.display_name} for server {guild_id or 'current'}"
        )

        if guild_id is None or guild_id.strip() == "":
            guild = interaction.guild
            if guild is None:
                await interaction.followup.send(
                    "Unable to retrieve current server information.",
                    ephemeral=True,
                )
                return
        else:
            if not guild_id.isdigit() or int(guild_id) <= 0:
                await interaction.followup.send(
                    "The provided server ID is invalid.", ephemeral=True
                )
                return
            guild = main_bot.get_guild(int(guild_id))
            if guild is None:
                await interaction.followup.send(
                    "The bot is not present in this server or the ID is incorrect.",
                    ephemeral=True,
                )
                return

        try:
            embed = discord.Embed(
                title=f"📊 Informations du serveur {guild.name}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow(),
            )

            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

            embed.add_field(name="🏷️ Nom", value=guild.name, inline=True)

            embed.add_field(name="🆔 ID", value=f"`{guild.id}`", inline=True)

            embed.add_field(
                name="👑 Propriétaire",
                value=(
                    f"{guild.owner.mention} ({guild.owner.name})"
                    if guild.owner
                    else "Inconnu"
                ),
                inline=True,
            )

            embed.add_field(
                name="👥 Membres",
                value=f"**{guild.member_count}** membres",
                inline=True,
            )

            embed.add_field(
                name="📅 Créé le",
                value=guild.created_at.strftime("%d/%m/%Y à %H:%M"),
                inline=True,
            )

            if guild.me:
                embed.add_field(
                    name="🤖 Bot rejoint le",
                    value=guild.me.joined_at.strftime("%d/%m/%Y à %H:%M"),
                    inline=True,
                )

            embed.add_field(
                name="🌍 Région",
                value=(
                    str(guild.preferred_locale)
                    if guild.preferred_locale
                    else "Inconnue"
                ),
                inline=True,
            )

            embed.add_field(
                name="🔒 Niveau de vérification",
                value=str(guild.verification_level).title(),
                inline=True,
            )

            embed.add_field(
                name="📢 Canaux", value=f"**{len(guild.channels)}** canaux", inline=True
            )

            embed.add_field(
                name="🎭 Rôles", value=f"**{len(guild.roles)}** rôles", inline=True
            )

            embed.set_footer(
                text=f"Demandé par {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url,
            )

            await interaction.followup.send(embed=embed)
        except discord.HTTPException as e:
            logger.error(
                f"HTTP error when executing guild-info command for {guild.id}: {e}"
            )
            await interaction.followup.send(
                "Error retrieving data. Please try again later.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error when executing guild-info command for {guild.id}: {e}"
            )
            await interaction.followup.send(
                "Unexpected error. Please try again later.", ephemeral=True
            )
