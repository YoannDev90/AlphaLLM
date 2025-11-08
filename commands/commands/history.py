import discord
import logging
from utils.config import logger_name
from utils.memory import get_memory_manager

logger = logging.getLogger(logger_name)

async def setup(bot: discord.Client):
    @bot.tree.command(name="clear-history", description="Reset your conversation history with the bot")
    async def clear_history(interaction: discord.Interaction):
        logger.info(f"Commande /clear-history exécutée par {interaction.user.display_name}")
        await interaction.response.defer(ephemeral=True)

        try:
            memory_manager = get_memory_manager()
            await memory_manager.clear_history(interaction.user.id)

            embed = discord.Embed(
                title="🗑️ History cleaned",
                description="Your conversation history has been deleted.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'historique: {str(e)}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while trying to clear your history. Please try again later.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
