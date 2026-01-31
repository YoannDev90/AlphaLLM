"""
Command for displaying system resource usage statistics
"""

import logging
from datetime import datetime, timedelta
from io import BytesIO

import discord
from discord import app_commands

from config import LOGGER_NAME
from utils.ressources import get_default_monitor

logger = logging.getLogger(LOGGER_NAME)


def _generate_cpu_graph(snapshots) -> BytesIO:
    """Generate CPU usage graph."""
    try:
        import matplotlib
        import matplotlib.pyplot as plt

        matplotlib.use("Agg")
    except ImportError:
        return None

    try:
        if len(snapshots) < 2:
            return None

        times = [s.timestamp for s in snapshots]
        cpu_percents = [
            float(s.cpu_percent) if s.cpu_percent is not None else 0 for s in snapshots
        ]

        fig, ax = plt.subplots(figsize=(10, 5), facecolor="black")
        ax.set_facecolor("black")
        ax.plot(times, cpu_percents, color="green", linewidth=2)
        ax.set_ylabel("CPU %", color="white")
        ax.grid(True, alpha=0.3, color="gray")
        ax.tick_params(colors="white")
        ax.set_xticklabels([])  # Hide X-axis timestamps

        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=160)
        buf.seek(0)
        plt.close(fig)
        return buf
    except Exception as e:
        logger.error(f"Error generating CPU graph: {e}")
        return None


def _generate_memory_graph(snapshots) -> BytesIO:
    """Generate memory usage graph."""
    try:
        import matplotlib
        import matplotlib.pyplot as plt

        matplotlib.use("Agg")
    except ImportError:
        return None

    try:
        if len(snapshots) < 2:
            return None

        times = [s.timestamp for s in snapshots]
        memories = [
            float(s.memory_percent) if s.memory_percent is not None else 0
            for s in snapshots
        ]

        fig, ax = plt.subplots(figsize=(10, 5), facecolor="black")
        ax.set_facecolor("black")
        ax.plot(times, memories, color="blue", linewidth=2)
        ax.set_ylabel("Memory %", color="white")
        ax.grid(True, alpha=0.3, color="gray")
        ax.tick_params(colors="white")
        ax.set_xticklabels([])  # Hide X-axis timestamps

        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=160)
        buf.seek(0)
        plt.close(fig)
        return buf
    except Exception as e:
        logger.error(f"Error generating memory graph: {e}")
        return None


async def setup(bot: discord.Client):
    """Setup the Resources Command"""

    @bot.tree.command(name="resources", description="Show system resource usage")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="Detailed Graphs", value="graphs"),
            app_commands.Choice(name="Text Mode Only", value="text"),
        ]
    )
    async def resources(interaction: discord.Interaction, mode: str = "graphs"):
        """Display current system resource usage"""
        logger.info(f"Command /resources exécutée par {interaction.user.display_name}")
        await interaction.response.defer()

        try:
            monitor = get_default_monitor()

            # Get snapshots from last 10 minutes
            all_snapshots = monitor.get_all_snapshots()
            ten_min_ago = datetime.now() - timedelta(minutes=10)
            recent_snapshots = [s for s in all_snapshots if s.timestamp >= ten_min_ago]

            # Get current usage
            current = monitor.get_current_usage()
            latest_snapshot = monitor.get_latest_snapshot()
            stats = monitor.get_statistics()

            if mode == "text":
                # Text mode only
                embed = discord.Embed(
                    title="📊 System Resources (Text Mode)",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow(),
                )

                # Current values
                if latest_snapshot:
                    cpu_percent = (
                        float(latest_snapshot.cpu_percent)
                        if latest_snapshot.cpu_percent
                        else 0
                    )
                    memory_percent = (
                        float(latest_snapshot.memory_percent)
                        if latest_snapshot.memory_percent
                        else 0
                    )

                    embed.add_field(
                        name="⚡ Current Usage",
                        value=(
                            f"**CPU:** {cpu_percent:.2f}% | {latest_snapshot.cpu_time:.2f}s\n"
                            f"**RAM:** {memory_percent:.1f}%"
                        ),
                        inline=False,
                    )

                # Averages from last 10 minutes
                if recent_snapshots:
                    cpu_percents = [
                        float(s.cpu_percent) for s in recent_snapshots if s.cpu_percent
                    ]
                    memories = [
                        float(s.memory_percent)
                        for s in recent_snapshots
                        if s.memory_percent
                    ]

                    avg_cpu = (
                        sum(cpu_percents) / len(cpu_percents) if cpu_percents else 0
                    )
                    avg_memory = sum(memories) / len(memories) if memories else 0

                    embed.add_field(
                        name="📈 Averages (10 min)",
                        value=(
                            f"**CPU Usage:** {avg_cpu:.2f}%\n"
                            f"**RAM Usage:** {avg_memory:.1f}%"
                        ),
                        inline=False,
                    )

                embed.set_footer(
                    text=f"Requested by {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar.url,
                )
                await interaction.followup.send(embed=embed)
                return

            elif mode == "graphs":
                # Send detailed graphs
                files = []
                embeds = []

                cpu_graph = _generate_cpu_graph(recent_snapshots)
                if cpu_graph:
                    files.append(discord.File(cpu_graph, filename="cpu.png"))
                    cpu_embed = discord.Embed(
                        title="CPU Usage", color=discord.Color.green()
                    )
                    cpu_embed.set_image(url="attachment://cpu.png")
                    embeds.append(cpu_embed)

                mem_graph = _generate_memory_graph(recent_snapshots)
                if mem_graph:
                    files.append(discord.File(mem_graph, filename="memory.png"))
                    mem_embed = discord.Embed(
                        title="Memory Usage", color=discord.Color.blue()
                    )
                    mem_embed.set_image(url="attachment://memory.png")
                    embeds.append(mem_embed)

                if files:
                    await interaction.followup.send(embeds=embeds, files=files)
                else:
                    await interaction.followup.send("No graphs available")

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des ressources: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Could not retrieve resource data: {str(e)}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
