"""
logger_bot.py

This module initializes and runs a secondary bot dedicated to logging activities.
It uses a custom logging handler to send logs to Discord.
"""

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from utils.logger_utils import setup_logging
import asyncio
import datetime

load_dotenv()

LOGGER_TOKEN = os.getenv("LOGGER_BOT_TOKEN")
LOGGER_PREFIX = os.getenv("LOGGER_BOT_PREFIX")

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

logger_bot = commands.Bot(command_prefix=LOGGER_PREFIX, intents=intents)
logger = setup_logging("AlphaLLM", logger_bot)

@logger_bot.event
async def on_ready():
    """
    Event triggered when the logger bot is ready and connected to Discord.
    Logs the bot's readiness.
    """
    logger.info(f'{logger_bot.user} est connecté !')
    await logger_bot.tree.sync()
    logger.info("Synchronisation des commandes du bot Logger...")

@logger_bot.tree.command(name="purge", description="Vide le MP avec le développeur")
async def purge(interaction: discord.Interaction):
    logger.info(f"Commande purge exécutée par {interaction.user.display_name}")
    try:
        dev_id = os.getenv("DEV_ID")
        dev_user = await logger_bot.fetch_user(dev_id)
        dm_channel = await dev_user.create_dm()
        await interaction.response.send_message("Suppression des messages en cours...", ephemeral=True)
        async for message in dm_channel.history(limit=None):
            await message.delete()
        logger.info("MP avec le développeur vidés avec succès.")
        await interaction.followup.send("Purge effectuée avec succès.", ephemeral=True)
    except discord.HTTPException as e:
        logger.error(f"Erreur lors de la purge : {e}")
        await interaction.followup.send("Une erreur est survenue lors de la purge.", ephemeral=True)

async def run_logger_bot():
    """
    Starts the logger bot and handles connection errors and unexpected exceptions.
    """
    try:
        await logger_bot.start(LOGGER_TOKEN)
        logger.info('Logger bot est en cours d\'exécution...')
    except discord.LoginFailure as e:
        logger.error(f"Erreur de connexion : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        await logger_bot.close()
