"""Health command handlers.

Provides a `setup` function to register the `/health` command which
performs runtime checks for subsystems and reports status.
"""

import time

import discord
from discord import app_commands

from cmds._shared import (defer_interaction, log_command_end,
                          log_command_error, log_command_start)
from core.tools import get_combined_tools, tools_loader
from managers.mcp import mcp_manager
from utils.logger import get_logger

logger = get_logger()


def _status_label(ok: bool) -> str:
    """Return a human-readable status label.

    Parameters
    ----------
    ok : bool
        True if the subsystem is healthy, False otherwise.

    Returns
    -------
    str
        "Healthy" when ok is True, otherwise "Degraded".
    """
    return "Healthy" if ok else "Degraded"


async def setup(tree: app_commands.CommandTree, bot):
    """Register the `health` command on the provided command tree.

    Parameters
    ----------
    tree : app_commands.CommandTree
        Command tree to register the command on.
    bot : Any
        Bot instance used to perform runtime checks.
    """

    @tree.command(name="health", description="Show runtime health for bot subsystems")
    async def health(interaction: discord.Interaction):
        """Perform runtime health checks and reply with a summary embed.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """
        start_time = time.perf_counter()
        log_command_start(logger, "health", interaction)

        await defer_interaction(interaction, ephemeral=True)
        logger.debug("Deferred interaction response")

        try:
            logger.debug("Starting health checks")
            gateway_ms = round(bot.latency * 1000, 2)

            # Discord readiness
            discord_ok = bot.is_ready()
            logger.debug(f"Discord readiness: {discord_ok}, latency: {gateway_ms}ms")

            # Memory health check
            memory_ok = True
            memory_note = "OK"
            memory_turns = 0
            try:
                memory_turns = len(bot.memory.list_turns(limit=1))
                logger.debug(f"Memory check passed: {memory_turns} turns found")
            except Exception as exc:
                memory_ok = False
                memory_note = f"Error: {exc}"
                logger.warning(f"Memory check failed: {exc}")

            # Tools health
            native_declared = len(tools_loader.tools_metadata)
            native_loaded = len(tools_loader.tools_handlers)
            tools_ok = native_loaded == native_declared
            logger.debug(
                f"Tools check: declared={native_declared}, loaded={native_loaded}"
            )

            combined_tools = get_combined_tools()
            mcp_tool_count = sum(
                1
                for tool in mcp_manager.tools_metadata
                if tool.get("function", {}).get("name", "").startswith("mcp_")
            )
            logger.debug(
                f"Tools summary: native={native_loaded}, mcp={mcp_tool_count}, total={len(combined_tools)}"
            )

            # MCP health
            configured_servers = len(mcp_manager.load_config().get("mcpServers", {}))
            connected_servers = len(mcp_manager.clients)
            mcp_ok = connected_servers == configured_servers
            logger.debug(
                f"MCP check: configured={configured_servers}, connected={connected_servers}"
            )

            overall_ok = discord_ok and memory_ok and tools_ok and mcp_ok

            embed = discord.Embed(
                title="Health Check",
                color=discord.Color.green() if overall_ok else discord.Color.orange(),
                description=f"Overall status: **{_status_label(overall_ok)}**",
            )

            embed.add_field(
                name="Discord",
                value=(
                    f"Status: {_status_label(discord_ok)}\nGateway latency: {gateway_ms} ms"
                ),
                inline=False,
            )

            embed.add_field(
                name="Memory",
                value=(
                    f"Status: {_status_label(memory_ok)}\n"
                    f"Recent turn probe: {memory_turns}\n"
                    f"Details: {memory_note}"
                ),
                inline=False,
            )

            embed.add_field(
                name="Tools",
                value=(
                    f"Status: {_status_label(tools_ok)}\n"
                    f"Native declared/loaded: {native_declared}/{native_loaded}\n"
                    f"MCP tools: {mcp_tool_count}\n"
                    f"Total model tools: {len(combined_tools)}"
                ),
                inline=False,
            )

            embed.add_field(
                name="MCP",
                value=(
                    f"Status: {_status_label(mcp_ok)}\n"
                    f"Configured servers: {configured_servers}\n"
                    f"Connected clients: {connected_servers}"
                ),
                inline=False,
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

            log_command_end(
                logger,
                "health",
                start_time,
                status=_status_label(overall_ok),
            )

        except Exception as exc:
            log_command_error(logger, "health", exc)
            try:
                await interaction.followup.send(
                    "Error during health check.", ephemeral=True
                )
            except Exception as send_exc:
                logger.error(
                    "Failed to send error message: %s", send_exc, exc_info=True
                )
