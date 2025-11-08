"""
Command for displaying system resource usage statistics
"""

import discord
import logging
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO
from datetime import datetime
from utils.config.app_config import logger_name
from utils.monitoring.resource import get_default_monitor

# Use non-interactive backend for matplotlib
matplotlib.use('Agg')

logger = logging.getLogger(logger_name)


def _generate_resource_graph() -> BytesIO:
    """
    Generate a graph of CPU and RAM usage over time (curves only, no axes/labels).
    
    Returns:
        BytesIO object containing the PNG image
    """
    try:
        monitor = get_default_monitor()
        snapshots = monitor.get_all_snapshots()
        
        if len(snapshots) < 2:
            return None
        
        # Extract data
        times = list(range(len(snapshots)))
        cpu_percents = [s.cpu_percent if s.cpu_percent is not None else 0 for s in snapshots]
        memories = [s.max_memory for s in snapshots]
        
        # Create figure with two y-axes - no padding
        fig, ax1 = plt.subplots(figsize=(10, 5), facecolor='#36393F')
        
        # CPU usage on left y-axis
        color_cpu = '#43B581'
        ax1.plot(times, cpu_percents, color=color_cpu, linewidth=2.5)
        ax1.set_facecolor('#36393F')
        
        # Memory usage on right y-axis
        ax2 = ax1.twinx()
        color_memory = '#7289DA'
        ax2.plot(times, memories, color=color_memory, linewidth=2.5)
        
        # Remove everything: axes, ticks, labels, grid, spines
        ax1.set_xticks([])
        ax1.set_xticklabels([])
        ax1.set_yticks([])
        ax1.set_yticklabels([])
        ax2.set_xticks([])
        ax2.set_xticklabels([])
        ax2.set_yticks([])
        ax2.set_yticklabels([])
        
        # Hide all spines
        for spine in ax1.spines.values():
            spine.set_visible(False)
        for spine in ax2.spines.values():
            spine.set_visible(False)
        
        # Remove title and grid
        ax1.grid(False)
        
        # Save to BytesIO with no padding
        buf = BytesIO()
        plt.savefig(buf, format='png', facecolor='#36393F', bbox_inches='tight', pad_inches=0, dpi=80)
        buf.seek(0)
        plt.close(fig)
        
        return buf
    
    except Exception as e:
        logger.error(f"Error generating resource graph: {e}")
        return None


async def setup(bot: discord.Client):
    """Setup the Resources Command"""
    
    @bot.tree.command(name="resources", description="Show system resource usage (CPU, RAM)")
    async def resources(interaction: discord.Interaction):
        """Display current system resource usage"""
        logger.info(f"Command /resources exécutée par {interaction.user.display_name}")
        await interaction.response.defer()
        
        try:
            monitor = get_default_monitor()
            
            # Get current usage
            current = monitor.get_current_usage()
            latest_snapshot = monitor.get_latest_snapshot()
            stats = monitor.get_statistics()
            
            # Create embed
            embed = discord.Embed(
                title="📊 System Resources",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            # Current Usage Section
            if current and latest_snapshot:
                cpu_percent_str = f"{latest_snapshot.cpu_percent:.2f}%" if latest_snapshot.cpu_percent is not None else "N/A"
                
                embed.add_field(
                    name="⚙️ Current Usage",
                    value=(
                        f"**CPU Time:** `{current.get('cpu_time_sec', 0):.2f}s`\n"
                        f"**CPU Usage:** `{cpu_percent_str}`\n"
                        f"**Max Memory:** `{current.get('max_memory_mb', 0):.1f}MB`\n"
                        f"**Timestamp:** `{current.get('timestamp', 'N/A')}`"
                    ),
                    inline=False
                )
                
                # CPU Details if available
                if latest_snapshot.cpu_user_time is not None:
                    embed.add_field(
                        name="🔧 CPU Details",
                        value=(
                            f"**User Time:** `{latest_snapshot.cpu_user_time:.4f}s`\n"
                            f"**System Time:** `{latest_snapshot.cpu_sys_time:.4f}s`\n"
                            f"**Voluntary Context Switches:** `{latest_snapshot.context_switches_vol}`\n"
                            f"**Involuntary Context Switches:** `{latest_snapshot.context_switches_invol}`"
                        ),
                        inline=False
                    )
                
                # Memory Details if available
                if latest_snapshot.page_faults_minor is not None:
                    embed.add_field(
                        name="💾 Memory Details",
                        value=(
                            f"**Page Faults (Minor):** `{latest_snapshot.page_faults_minor}`\n"
                            f"**Page Faults (Major):** `{latest_snapshot.page_faults_major}`\n"
                            f"**Swaps:** `{latest_snapshot.swaps}`"
                        ),
                        inline=False
                    )
                
                # I/O Details if available
                if latest_snapshot.io_reads is not None:
                    embed.add_field(
                        name="💿 I/O Operations",
                        value=(
                            f"**Block Reads:** `{latest_snapshot.io_reads}`\n"
                            f"**Block Writes:** `{latest_snapshot.io_writes}`"
                        ),
                        inline=False
                    )
            
            # Statistics Section
            if stats and stats.get('samples_count', 0) > 0:
                cpu_percent_avg = f"{stats.get('cpu_percent_avg', 0):.2f}%" if 'cpu_percent_avg' in stats else "N/A"
                cpu_percent_max = f"{stats.get('cpu_percent_max', 0):.2f}%" if 'cpu_percent_max' in stats else "N/A"
                
                embed.add_field(
                    name="📈 Statistics",
                    value=(
                        f"**Samples:** `{stats['samples_count']}`\n"
                        f"**CPU Time - Avg/Max:** `{stats['cpu_time_avg']:.2f}s / {stats['cpu_time_max']:.2f}s`\n"
                        f"**CPU % - Avg/Max:** `{cpu_percent_avg} / {cpu_percent_max}`\n"
                        f"**Memory - Min/Max/Avg:** `{stats['memory_min']:.1f}MB / {stats['memory_max']:.1f}MB / {stats['memory_avg']:.1f}MB`"
                    ),
                    inline=False
                )
            
            embed.set_footer(
                text=f"Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Generate and attach graph
            graph_buffer = _generate_resource_graph()
            if graph_buffer:
                file = discord.File(graph_buffer, filename="Resources.png")
                embed.set_image(url="attachment://Resources.png")
                
                # Add legend as a field below the image
                embed.add_field(
                    name="📈 Graph Legend",
                    value=(
                        f"🟢 **Green Curve:** CPU Usage (%)\n"
                        f"🔵 **Blue Curve:** Memory Usage (MB)"
                    ),
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des ressources: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Could not retrieve resource data: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
