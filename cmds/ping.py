"""Ping command handlers.

Provides a `setup` function to register the `/ping` command which
returns the bot's gateway latency.
"""

import time

import discord
from discord import app_commands

from cmds._shared import log_command_end, log_command_error, log_command_start
from utils.logger import get_logger

logger = get_logger()


async def setup(tree: app_commands.CommandTree, bot):
    """Register the `ping` command on the given command tree.

    Parameters
    ----------
    tree : app_commands.CommandTree
        Command tree to register the command on.
    bot : Any
        Bot instance used to read gateway latency.
    """

    @tree.command(name="ping", description="Check bot latency and responsiveness")
    async def ping(interaction: discord.Interaction):
        """Respond with gateway latency.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """

        start_time = time.perf_counter()
        log_command_start(logger, "ping", interaction)

        try:
            gateway_ms = round(bot.latency * 1000, 2)

            embed = discord.Embed(
                title="Pong!",
                color=discord.Color.blurple(),
                description="Bot is responsive.",
            )
            embed.add_field(
                name="Gateway Latency", value=f"{gateway_ms} ms", inline=True
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

            log_command_end(logger, "ping", start_time)
        except Exception as exc:
            log_command_error(logger, "ping", exc)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Error while checking latency.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "Error while checking latency.", ephemeral=True
                )
