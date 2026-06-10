import time

from discord import app_commands

from cmds._shared import (defer_interaction, log_command_end,
                          log_command_error, log_command_start,
                          send_interaction)
from utils.logger import get_logger

logger = get_logger()


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(
        name="set-mood", description="Change the mood/personality of the AlphaLLM"
    )
    @app_commands.describe(mood="Desired mood")
    @app_commands.choices(
        mood=[
            app_commands.Choice(name="Sarcastic", value="sarcastic"),
            app_commands.Choice(name="Aggressive", value="aggressive"),
            app_commands.Choice(name="Evil Mastermind", value="mastermind"),
            app_commands.Choice(name="Nihilist", value="nihilist"),
            app_commands.Choice(name="Chaotic Jester", value="jester"),
        ]
    )
    async def set_mood(interaction, mood: str):
        start_time = time.perf_counter()
        log_command_start(logger, "set_mood", interaction, mood=mood)

        await defer_interaction(interaction, ephemeral=True)

        try:
            await bot.memory.set_metadata_and_sync(interaction.user.id, "mood", mood)
            mood_names = {
                "sarcastic": "Sarcastic",
                "aggressive": "Aggressive",
                "mastermind": "Evil Mastermind",
                "nihilist": "Nihilist",
                "jester": "Chaotic Jester",
            }
            await send_interaction(
                interaction,
                content=(
                    f"Mood changed to: **{mood_names[mood]}**. Prepare yourself for the consequences."
                ),
                ephemeral=True,
            )
            log_command_end(logger, "set_mood", start_time)
        except Exception as exc:
            log_command_error(logger, "set_mood", exc)
            await interaction.followup.send(
                "Error while updating mood.", ephemeral=True
            )
