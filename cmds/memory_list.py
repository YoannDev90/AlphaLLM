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
        name="memory-list", description="List the most recent turns in memory"
    )
    @app_commands.describe(
        limit="Number of turns to display", user="Target user (optional)"
    )
    async def memory_list(
        interaction: discord.Interaction,
        limit: int = 10,
        user: Optional[discord.User] = None,
    ):
        start_time = time.perf_counter()
        log_command_start(logger, "memory_list", interaction, limit=limit)

        await defer_interaction(interaction, ephemeral=True)

        target_user = user or interaction.user
        try:
            if (
                target_user.id != interaction.user.id
                and not interaction.user.guild_permissions.manage_messages
            ):
                logger.warning(
                    "Permission denied for /memory_list by user=%s target=%s",
                    interaction.user.id,
                    target_user.id,
                )
                await interaction.followup.send(
                    "You don't have permission to view another user's memory.",
                    ephemeral=True,
                )
                return

            turns = bot.memory.list_turns(target_user.id, limit=max(1, min(limit, 20)))
            if not turns:
                await interaction.followup.send(
                    "No turns in memory for this account.", ephemeral=True
                )
                log_command_end(logger, "memory_list", start_time, status="empty")
                return

            def _format_turn(turn):
                created = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(turn.created_at)
                )
                user_snippet = turn.user_content.replace("\n", " ")[:120]
                assistant_snippet = (turn.assistant_content or "").replace("\n", " ")[
                    :120
                ]
                lines = [
                    f"{turn.turn_id[:8]} | {created} | {turn.user_name} ({turn.user_id})",
                    f"  user: {user_snippet}",
                ]
                if assistant_snippet:
                    lines.append(f"  bot: {assistant_snippet}")
                return "\n".join(lines)

            content = "\n\n".join(_format_turn(turn) for turn in turns)
            if len(content) > 1900:
                content = content[:1900] + "\n..."
            await send_interaction(
                interaction, content=f"```text\n{content}\n```", ephemeral=True
            )
            log_command_end(logger, "memory_list", start_time)
        except Exception as exc:
            log_command_error(logger, "memory_list", exc)
            await interaction.followup.send(
                "Error while listing memory turns.", ephemeral=True
            )
