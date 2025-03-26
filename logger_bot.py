"""
logger_bot.py

This module initializes and runs a secondary bot dedicated to logging activities.
It uses a custom logging handler to send logs to Discord.
"""

#logs/logger_bot.py

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
