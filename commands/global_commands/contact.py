import discord
import logging
from dotenv import load_dotenv
from utils.langs import get_language, get_translation as tlt
import os

load_dotenv()
logger = logging.getLogger('AlphaLLM')

async def setup(bot: discord.Client):
    @bot.tree.command(name="contact", description="Envoie un message au développeur")
    async def contact(interaction: discord.Interaction, message: str):
        logger.info(f"Commande contact exécutée par {interaction.user.display_name}")
        
        user_lang = get_language(interaction.user.id)
        
        try:
            dev_id = os.getenv("DEV_ID")
            dev_user = await bot.fetch_user(dev_id)
            await dev_user.send(f"<@{interaction.user.id}> ({interaction.user}): {message}")
            await interaction.response.send_message(tlt(language=user_lang, key="contact_success"), ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(tlt(language=user_lang, key="contact_error"), ephemeral=True)
            return
