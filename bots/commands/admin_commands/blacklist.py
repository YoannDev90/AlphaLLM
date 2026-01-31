import logging
import re
from datetime import datetime

import discord

from config import DEV_IDS, LOGGER_NAME
from utils.database.blacklist import add_to_blacklist, remove_from_blacklist
from utils.database.perms_conf import get_blacklist

logger = logging.getLogger(LOGGER_NAME)

CHOICES = [
    discord.app_commands.Choice(name="show", value=0),
    discord.app_commands.Choice(name="add", value=1),
    discord.app_commands.Choice(name="remove", value=2),
]


async def setup(bot: discord.Client):
    @bot.tree.command(name="blacklist", description="Add a user to the blacklist")
    @discord.app_commands.choices(mode=CHOICES)
    async def blacklist(
        interaction: discord.Interaction,
        mode: discord.app_commands.Choice[int],
        user_id: str = None,
        reason: str = "Aucune raison fournie",
        log_text: str = None,
    ):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message(
                "❌ You are not authorized to use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(
            f"Command /blacklist [{mode.name}] executed by {interaction.user.display_name}"
        )

        match mode.value:
            case 0:
                blacklisted_users = await get_blacklist(details=True)
                if not blacklisted_users:
                    await interaction.followup.send(
                        "No users are currently blacklisted.",
                        ephemeral=True,
                    )
                    return

                embed = discord.Embed(
                    title="📋 List of blacklisted users",
                    color=discord.Color.red(),
                    timestamp=datetime.now(),
                )
                embed.set_footer(text=f"Total: {len(blacklisted_users)} user(s)")

                for user_data in blacklisted_users:
                    user_id = user_data[0]
                    reason = user_data[1]
                    ban_date = user_data[2]

                    try:
                        date_obj = datetime.fromisoformat(
                            ban_date.replace("Z", "+00:00")
                        )
                        formatted_date = date_obj.strftime("%d/%m/%Y à %H:%M")
                    except Exception:
                        formatted_date = ban_date

                    try:
                        user = await bot.fetch_user(user_id)
                        username = user.global_name if user.global_name else user.name
                    except Exception:
                        username = f"User (ID: {user_id})"

                    field_value = f"**Reason:** {reason}\n**Date:** {formatted_date}\n```\n{user_id}\n```"
                    embed.add_field(
                        name=f"👤 {username}", value=field_value, inline=False
                    )

                await interaction.followup.send(embed=embed)
            case 1:
                # Extract user ID from log_text if provided
                if log_text:
                    # Find all potential Discord IDs (15-20 digit numbers)
                    potential_ids = re.findall(r"\b\d{15,20}\b", log_text)
                    if not potential_ids:
                        await interaction.followup.send(
                            "No valid user ID found in the provided log.",
                            ephemeral=True,
                        )
                        return
                    # Use the first valid-looking ID
                    extracted_id = potential_ids[0]
                    if user_id and user_id != extracted_id:
                        await interaction.followup.send(
                            f"ID conflict: provided `{user_id}`, extracted from log `{extracted_id}`. Please specify only one ID.",
                            ephemeral=True,
                        )
                        return
                    user_id = extracted_id

                if not user_id or not user_id.isdigit() or int(user_id) <= 0:
                    await interaction.followup.send(
                        "The provided user ID is invalid.", ephemeral=True
                    )
                    return
                await add_to_blacklist(int(user_id), reason)
                user = await bot.fetch_user(int(user_id))
                if user is None:
                    await interaction.followup.send("User not found.", ephemeral=True)
                    return
                await interaction.followup.send(
                    f"User {user.name} (ID `{user_id}`) has been added to the blacklist for reason: `{reason}`."
                )
            case 2:
                # Extract user ID from log_text if provided
                if log_text:
                    # Find all potential Discord IDs (15-20 digit numbers)
                    potential_ids = re.findall(r"\b\d{15,20}\b", log_text)
                    if not potential_ids:
                        await interaction.followup.send(
                            "No valid user ID found in the provided log.",
                            ephemeral=True,
                        )
                        return
                    # Use the first valid-looking ID
                    extracted_id = potential_ids[0]
                    if user_id and user_id != extracted_id:
                        await interaction.followup.send(
                            f"ID conflict: provided `{user_id}`, extracted from log `{extracted_id}`. Please specify only one ID.",
                            ephemeral=True,
                        )
                        return
                    user_id = extracted_id

                if not user_id.isdigit() or int(user_id) <= 0:
                    await interaction.followup.send(
                        "The provided user ID is invalid.", ephemeral=True
                    )
                    return
                await remove_from_blacklist(int(user_id))
                await interaction.followup.send(
                    f"User with ID `{user_id}` has been removed from the blacklist.",
                    ephemeral=True,
                )
