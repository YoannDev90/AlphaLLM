
import discord
from discord import app_commands
import logging
from utils.config import logger_name
from embeds.install_embed import InstallView, create_install_embed

logger = logging.getLogger(logger_name)

async def setup(bot: discord.Client):
    @bot.tree.command(name="install", description="Display invitation links to install AlphaLLM bots")
    @app_commands.default_permissions(manage_guild=True)
    async def install(interaction: discord.Interaction):
        logger.info(f"Commande /install exécutée par {interaction.user.display_name}")
        
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You must have server management permissions to use this command.", ephemeral=True)
            return
        
        try:
            embed = create_install_embed(interaction.user)
            
            view = InstallView()
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message d'installation: {str(e)}")
            await interaction.response.send_message("❌ An error occurred while displaying the installation links.", ephemeral=True)