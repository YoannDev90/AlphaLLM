import discord
from discord import app_commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="contact", description="Contact the developer")
    @app_commands.describe(message="Your message to the developer")
    async def contact(interaction: discord.Interaction, message: str):
        logger.info(f"Commande /contact exécutée par {interaction.user.display_name}")
        
        try:
            dev_id = os.getenv("DEV_ID")
            dev_user = await bot.fetch_user(dev_id)
            await dev_user.send(f"<@{interaction.user.id}> ({interaction.user.global_name}): {message}")
            await interaction.response.send_message("Message sent successfully to the developer.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message("Failed to send message to the developer.", ephemeral=True)
            return
