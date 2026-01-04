import asyncio
import logging
import os

import discord
from discord.ext import commands

from bots.commands.cmds import setup_commands
from config import BOT_TOKEN, DEBUG, DEV_IDS, LOGGER_NAME
from utils.discord_utils.commands_ids import command_id_manager
from utils.handlers.messages import smart_long_messages
from utils.unified_text import Origin, Text_Model, unified_text_gen

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", owner_ids=DEV_IDS, intents=intents)
logger = logging.getLogger(LOGGER_NAME)

logging.getLogger('discord.ext.commands').setLevel(logging.CRITICAL)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    activity = discord.CustomActivity(name="🤖 Try @AlphaLLM or /commands")
    await bot.change_presence(activity=activity, status=discord.Status.idle)
    await bot.tree.sync()
    command_id_manager.set_bot(bot)
    # Fetch in background
    asyncio.create_task(command_id_manager.fetch_command_ids())
    logger.info("Fetch des IDs de commandes lancé en arrière-plan")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    files = []
    if message.attachments:
        for attachment in message.attachments:
            files.append(attachment.url)
    
    response = [result async for result in unified_text_gen(
        user_id=message.author.id,
        conv_id=message.channel.id,
        input=message.content,
        model=Text_Model.AUTO,
        files=files if files else None,
        origin=Origin.DISCORD,
        message=message,
        bot=bot,
        stream=False
    )]
    result = response[0]
    async with message.channel.typing():
        await smart_long_messages(message.channel, result.response)


async def run_bot():
    mode_label = "BetaLLM" if DEBUG else "AlphaLLM"
    await setup_commands(bot, is_admin_bot=False)
    logger.info(f"Starting {mode_label}")
    try:
        logger.info("Logging in...")
        await bot.start(BOT_TOKEN)
    except discord.LoginFailure as exc:
        logger.error(f"Login failure {exc}")
    except Exception as exc:
        logger.error(f"Bot runtime failure {exc}")
    finally:
        if not bot.is_closed():
            await bot.close()
        logger.info("Bot stopped")