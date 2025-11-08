import discord
from discord import app_commands
from utils import command_id_manager
import logging
from utils.config import logger_name

logger = logging.getLogger(logger_name)

async def setup(bot: discord.Client):
    @bot.tree.command(name="help-bot", description="Show help informations")
    async def help(interaction: discord.Interaction):
        logger.info(f"Commande /help-bot exécutée par {interaction.user.display_name}")

        desc = f"Here's how to use the bot:\n💬 - To chat, debate, play, ... with me, simply mention me in your messages ( <@{bot.user.id}> ).\n🖼️ - To generate images, use the {command_id_manager.get_command_mention('image')} command.\n📜 - To see the list of available commands, use `/commands`.\n🔗 - To chat with my developer or request help with the bot, use {command_id_manager.get_command_mention('support')}."

        try:
            embed = discord.Embed(
                title="Help - AlphaLLM",
                description=desc,
                color=discord.Color.default(),
                timestamp=discord.utils.utcnow()
            )

            embed.set_footer(text=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error sending help message: {str(e)}")
            await interaction.followup.send("❌ An error occurred while sending the help message.", ephemeral=True)
