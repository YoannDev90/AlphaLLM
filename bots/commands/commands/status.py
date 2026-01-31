import logging

import discord

from config import LOGGER_NAME
from utils.discord_utils.status import get_status

logger = logging.getLogger(LOGGER_NAME)


async def setup(bot: discord.Client):
    @bot.tree.command(name="status", description="Show the status of the bot")
    async def status(interaction: discord.Interaction):
        logger.info(f"Command /status executed by {interaction.user.display_name}")

        status_data = get_status()

        embed = discord.Embed(
            title="🤖 Models Status",
            description="Current status of all AI models:",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )

        if not status_data:
            embed.add_field(
                name="❌ No Data",
                value="No status data available yet. Please wait for the next status check.",
                inline=False,
            )
        else:
            for model, data in status_data.items():
                status_emoji = {
                    "online": "🟢",
                    "degraded": "🟡",
                    "offline": "🔴",
                    "unknown": "⚪",
                }.get(data.get("status", "unknown"), "⚪")

                success_rate = data.get("success_rate", 0)
                total_requests = data.get("total_requests", 0)
                last_check = data.get("last_check", 0)

                # Format last check time
                if last_check > 0:
                    last_check_str = f"<t:{int(last_check)}:R>"
                else:
                    last_check_str = "Never"

                value = f"**Status:** {status_emoji} {data.get('status', 'unknown').title()}\n"
                value += f"**Success Rate:** {success_rate:.1f}%\n"
                value += f"**Total Requests:** {total_requests}\n"
                value += f"**Last Check:** {last_check_str}"

                embed.add_field(
                    name=f"🤖 {model.title()}",
                    value=value,
                    inline=False,
                )

        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)
