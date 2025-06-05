import discord
from discord import app_commands
import logging

logger = logging.getLogger('AlphaLLM')



async def setup(bot: discord.Client):
    @bot.tree.command(name="help-bot", description="Show help informations")
    async def help(interaction: discord.Interaction):
        logger.info(f"Commande /help-bot exécutée par {interaction.user.display_name}")

        desc = "Here's how to use the bot:\n💬 - To chat, debate, play, ... with me, simply mention me in your messages ( <@1286951908786962442> ).\n🖼️ - To generate images, use the `/image` command.\n📜 - To see the list of available commands, use `/commands`.\n🔗 - To chat with my developer or request help with the bot, use `/support`."

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
