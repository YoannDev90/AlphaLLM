import time
from typing import Optional

import discord
from discord import app_commands

from cmds._shared import (defer_interaction, log_command_end,
                          log_command_error, log_command_start,
                          send_interaction)
from utils.logger import get_logger

logger = get_logger()


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(
        name="memory-clear", description="Clear the conversation history for a user"
    )
    @app_commands.describe(user="Target user (optional)")
    async def memory_clear(
        interaction: discord.Interaction,
        user: Optional[discord.User] = None,
    ):
        start_time = time.perf_counter()
        log_command_start(logger, "memory_clear", interaction)

        await defer_interaction(interaction, ephemeral=True)

        target_user = user or interaction.user
        try:
            if (
                target_user.id != interaction.user.id
                and not interaction.user.guild_permissions.manage_messages
            ):
                logger.warning(
                    "Permission denied for /memory_clear by user=%s target=%s",
                    interaction.user.id,
                    target_user.id,
                )
                await interaction.followup.send(
                    "You don't have permission to clear another user's memory.",
                    ephemeral=True,
                )
                return

            removed = await bot.memory.clear_history_and_sync(target_user.id)
            await send_interaction(
                interaction,
                content=f"{removed} turn(s) deleted for {target_user.display_name}.",
                ephemeral=True,
            )
            log_command_end(logger, "memory_clear", start_time)
        except Exception as exc:
            log_command_error(logger, "memory_clear", exc)
            await interaction.followup.send(
                "Error while clearing memory.", ephemeral=True
            )
