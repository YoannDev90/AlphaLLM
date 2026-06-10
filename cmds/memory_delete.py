import time

from discord import app_commands

from cmds._shared import (defer_interaction, log_command_end,
                          log_command_error, log_command_start,
                          send_interaction)
from utils.logger import get_logger

logger = get_logger()


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(
        name="memory-delete",
        description="Delete a specific turn from conversation history",
    )
    @app_commands.describe(turn_id="Turn ID to delete")
    async def memory_delete(interaction, turn_id: str):
        start_time = time.perf_counter()
        log_command_start(logger, "memory_delete", interaction, turn_id=turn_id)

        await defer_interaction(interaction, ephemeral=True)

        try:
            try:
                turn = bot.memory.get_turn(turn_id)
            except KeyError:
                logger.warning("Turn not found for /memory_delete: %s", turn_id)
                await interaction.followup.send("Turn ID not found.", ephemeral=True)
                return

            if (
                turn.user_id != interaction.user.id
                and not interaction.user.guild_permissions.manage_messages
            ):
                logger.warning(
                    "Permission denied for /memory_delete by user=%s target_turn_user=%s",
                    interaction.user.id,
                    turn.user_id,
                )
                await interaction.followup.send(
                    "You don't have permission to delete another user's memory.",
                    ephemeral=True,
                )
                return

            deleted = await bot.memory.delete_turn_and_sync(turn.turn_id)
            await send_interaction(
                interaction,
                content=f"Turn `{deleted.turn_id[:8]}` deleted.",
                ephemeral=True,
            )
            log_command_end(logger, "memory_delete", start_time)
        except Exception as exc:
            log_command_error(logger, "memory_delete", exc)
            await interaction.followup.send(
                "Error while deleting memory turn.", ephemeral=True
            )
