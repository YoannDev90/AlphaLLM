import time

import discord
from discord import app_commands

from cmds._shared import (defer_interaction, log_command_end,
                          log_command_error, log_command_start,
                          send_interaction)
from core.tools import get_combined_tools
from utils.logger import get_logger

logger = get_logger()


async def setup(tree: app_commands.CommandTree, bot):
    @tree.command(
        name="list-tools", description="List all tools available to the model"
    )
    async def list_tools(interaction):
        start_time = time.perf_counter()
        log_command_start(logger, "list-tools", interaction)

        await defer_interaction(interaction, ephemeral=False)

        try:
            tools = get_combined_tools()

            if not tools:
                embed = discord.Embed(
                    title="No tools available", color=discord.Color.red()
                )
                await send_interaction(interaction, embed=embed, ephemeral=False)
                log_command_end(logger, "list-tools", start_time, status="empty")
                return

            # Normalize tool descriptors to a common shape {name, description, raw}
            normalized = []
            for t in tools:
                try:
                    if (
                        isinstance(t, dict)
                        and t.get("type") == "function"
                        and isinstance(t.get("function"), dict)
                    ):
                        fn = t["function"]
                        name = fn.get("name")
                        desc = fn.get("description", "No description")
                    else:
                        name = t.get("name") if isinstance(t, dict) else None
                        desc = (
                            t.get("description", "No description")
                            if isinstance(t, dict)
                            else str(t)
                        )
                    if not name:
                        # skip malformed entries
                        continue
                    normalized.append({"name": name, "description": desc, "raw": t})
                except Exception:
                    continue

            # Group tools by category
            native_tools = [t for t in normalized if not t["name"].startswith("mcp_")]
            mcp_tools = [t for t in normalized if t["name"].startswith("mcp_")]

            embeds = []

            # Native tools embed
            if native_tools:
                embed = discord.Embed(
                    title="🔧 Native Tools",
                    color=discord.Color.blurple(),
                    description="Built-in sandboxed execution tools",
                )
                for tool in native_tools:
                    desc = tool.get("description", "No description")
                    embed.add_field(name=f"`{tool['name']}`", value=desc, inline=False)
                embeds.append(embed)

            # MCP tools embed(s)
            if mcp_tools:
                current_embed = discord.Embed(
                    title="🔌 MCP Tools",
                    color=discord.Color.green(),
                    description="Model Context Protocol tools",
                )
                field_count = 0

                for tool in mcp_tools:
                    desc = tool.get("description", "No description")
                    current_embed.add_field(
                        name=f"`{tool['name']}`", value=desc, inline=False
                    )
                    field_count += 1

                    # Discord embeds have a max of 25 fields, create new embed if needed
                    if field_count >= 25:
                        embeds.append(current_embed)
                        current_embed = discord.Embed(
                            title="🔌 MCP Tools (continued)",
                            color=discord.Color.green(),
                        )
                        field_count = 0

                if field_count > 0:
                    embeds.append(current_embed)

            # Send embeds
            await send_interaction(interaction, embeds=embeds[:10], ephemeral=False)
            for embed in embeds[10:]:
                await interaction.followup.send(embed=embed)

            log_command_end(logger, "list-tools", start_time)
        except Exception as exc:
            log_command_error(logger, "list-tools", exc)
            await interaction.followup.send(
                "Error while listing tools.", ephemeral=False
            )
