# import discord
# import logging
# from config import LOGGER_NAME
# from utils.monitoring.status import get_status

# logger = logging.getLogger(LOGGER_NAME)

# async def setup(bot: discord.Client):
#     @bot.tree.command(name="status", description="Show the status of all bots")
#     async def status(interaction: discord.Interaction):
#         logger.info(f"Commande /status exécutée par {interaction.user.display_name}")
#         await interaction.response.defer()

#         bot_statuses = get_status()

#         embed = discord.Embed(
#             title="🤖 Bot Status Dashboard",
#             color=discord.Color.blue(),
#             timestamp=discord.utils.utcnow()
#         )

#         for bot_name, status_info in bot_statuses.items():
#             ping = status_info.get("ping", 0)
#             state = status_info.get("status", "offline")
            
#             if state == "online":
#                 color_indicator = "✅"
#             elif state == "degraded":
#                 color_indicator = "⚠️"
#             else:
#                 color_indicator = "❌"
            
#             if ping > 0:
#                 value = f"{color_indicator} {state.capitalize()}\n⚡️ {ping}ms"
#             else:
#                 value = f"{color_indicator} {state.capitalize()}"
            
#             embed.add_field(
#                 name=f"**{bot_name}**\t",
#                 value=value,
#                 inline=True
#             )

#         embed.set_footer(
#             text=f"Requested by {interaction.user.display_name}",
#             icon_url=interaction.user.display_avatar.url
#         )

#         await interaction.followup.send(embed=embed)