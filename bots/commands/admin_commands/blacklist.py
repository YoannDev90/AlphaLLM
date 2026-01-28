import asyncio
import logging
from datetime import datetime

import discord

from config import LOGGER_NAME
from utils.database.blacklist import add_to_blacklist, remove_from_blacklist
from utils.database.perms_conf import get_blacklist

logger = logging.getLogger(LOGGER_NAME)

CHOICES = [
    discord.app_commands.Choice(name="show", value=0),
    discord.app_commands.Choice(name="add", value=1),
    discord.app_commands.Choice(name="remove", value=2),
]


async def setup(bot: discord.Client):
    @bot.tree.command(
        name="blacklist", description="Ajoute un utilisateur à la blacklist"
    )
    @discord.app_commands.choices(mode=CHOICES)
    async def blacklist(
        interaction: discord.Interaction,
        mode: discord.app_commands.Choice[int],
        user_id: str = None,
        reason: str = "Aucune raison fournie",
    ):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(
            f"Commande /blacklist [{mode.name}] exécutée par {interaction.user.display_name}"
        )

        match mode.value:
            case 0:
                blacklisted_users = await get_blacklist(details=True)
                if not blacklisted_users:
                    await interaction.followup.send(
                        "Aucun utilisateur n'est actuellement blacklisté.",
                        ephemeral=True,
                    )
                    return

                embed = discord.Embed(
                    title="📋 Liste des utilisateurs blacklistés",
                    color=discord.Color.red(),
                    timestamp=datetime.now(),
                )
                embed.set_footer(text=f"Total: {len(blacklisted_users)} utilisateur(s)")

                for user_data in blacklisted_users:
                    user_id = user_data[0]
                    reason = user_data[1]
                    ban_date = user_data[2]

                    try:
                        date_obj = datetime.fromisoformat(
                            ban_date.replace("Z", "+00:00")
                        )
                        formatted_date = date_obj.strftime("%d/%m/%Y à %H:%M")
                    except:
                        formatted_date = ban_date

                    try:
                        user = await bot.fetch_user(user_id)
                        username = user.global_name if user.global_name else user.name
                    except:
                        username = f"Utilisateur (ID: {user_id})"

                    field_value = f"**Raison:** {reason}\n**Date:** {formatted_date}\n```\n{user_id}\n```"
                    embed.add_field(
                        name=f"👤 {username}", value=field_value, inline=False
                    )

                await interaction.followup.send(embed=embed)
            case 1:
                if not user_id.isdigit() or int(user_id) <= 0:
                    await interaction.followup.send(
                        "L'ID utilisateur fourni est invalide.", ephemeral=True
                    )
                    return
                await add_to_blacklist(int(user_id), reason)
                user = await bot.fetch_user(int(user_id))
                if user is None:
                    await interaction.followup.send(
                        "Utilisateur introuvable.", ephemeral=True
                    )
                    return
                await interaction.followup.send(
                    f"L'utilisateur {user.name} (ID `{user_id}`) a été ajouté à la liste noire pour la raison : `{reason}`."
                )
            case 2:
                if not user_id.isdigit() or int(user_id) <= 0:
                    await interaction.followup.send(
                        "L'ID utilisateur fourni est invalide.", ephemeral=True
                    )
                    return
                await remove_from_blacklist(int(user_id))
                await interaction.followup.send(
                    f"L'utilisateur avec l'ID `{user_id}` a été retiré de la liste noire.",
                    ephemeral=True,
                )
