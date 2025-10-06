import discord
from discord import app_commands
import logging
from utils.config import logger_name
from typing import Literal
from embeds.uninstall import UninstallConfirmView, create_uninstall_embed, bot_ids

logger = logging.getLogger(logger_name)

async def setup(bot: discord.Client):
    @bot.tree.command(name="uninstall", description="Remove an AlphaLLM bot from the server")
    @app_commands.describe(
        bot_name="The bot to remove from the server",
        delete_messages="Whether to delete the bot's messages from the last 14 days"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def uninstall(
        interaction: discord.Interaction,
        bot_name: Literal["ChatGPT", "DeepSeek", "EvilGPT", "Gemini", "Grok", "Llama", "Mistral", "Phi", "Perplexity", "Qwen"],
        delete_messages: bool = False
    ):
        logger.info(f"Commande /uninstall exécutée par {interaction.user.display_name} pour le bot {bot_name}")
        
        # Vérifier les permissions
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You must have server management permissions to use this command.", ephemeral=True)
            return
        
        bot_id = bot_ids[bot_name]
        
        # Créer l'embed de confirmation
        embed = create_uninstall_embed(interaction.user, bot_name, bot_id, delete_messages)
        
        # Créer la vue de confirmation
        view = UninstallConfirmView(bot_name, bot_id, delete_messages)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
