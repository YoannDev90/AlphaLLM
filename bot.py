"""
bot.py

This module initializes and runs the main Discord bot. It handles events such as
bot readiness and incoming messages, and processes AI responses for user queries.
"""

#bot.py

import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
from cmds import setup_commands
from utils.ai_process import process_ai_response
from utils.langs import get_translation as tlt
from datetime import datetime, timedelta


load_dotenv()

IS_TESTBOT = True

if IS_TESTBOT:
    TOKEN = os.getenv("TESTBOT_TOKEN")
else:
    TOKEN = os.getenv("BOT_TOKEN")
PREFIX = os.getenv("BOT_PREFIX")

intents = discord.Intents.all()
intents.presences = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)
logger = logging.getLogger("AlphaLLM")

@bot.event
async def on_ready():
    """
    Event triggered when the bot is ready and connected to Discord.
    Logs the bot's readiness and syncs application commands.
    """
    logger.info(f'{bot.user} connecté !')
    activity = discord.CustomActivity(name="🌍 alphallm.fr.nf")
    await bot.change_presence(activity=activity, status=discord.Status.idle)
    logger.info("Statut mis à jour")
    logger.info("Synchronisation des commandes...")
    await bot.tree.sync()

@bot.event
async def on_message(message):
    """
    Event triggered when a message is sent in a text channel.
    Processes messages that mention the bot and sends AI-generated responses.

    Args:
        message (discord.Message): The message object containing the content and metadata.
    """
    if not message.author.bot and message.channel.type == discord.ChannelType.text:
        logger.debug(f"Message reçu de {message.author}: {message.content}")
        await process_ai_response(message)

async def run_bot():
    """
    Starts the bot and sets up commands. Handles connection errors and unexpected exceptions.
    """
    logger.info("Démarrage du bot en cours...")
    await setup_commands(bot)
    logger.info("Configuration des commandes terminée")
    try:
        await bot.start(TOKEN)
        logger.info(f'{bot.user} connecté !')
    except discord.LoginFailure as e:
        logger.error(f"Erreur de connexion : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        await bot.close()