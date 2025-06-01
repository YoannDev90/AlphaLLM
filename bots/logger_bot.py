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

logger_bot = commands.Bot(command_prefix=LOGGER_PREFIX, intents=intents)
logger = setup_logging("AlphaLLM", logger_bot)

@logger_bot.event
async def on_ready():
    activity = discord.CustomActivity(name="🎛️ Monitoring AlphaLLM")
    await logger_bot.change_presence(activity=activity)
    await logger_bot.tree.sync()

@logger_bot.tree.command(name="purge")
async def purge(interaction: discord.Interaction):
    logger.info(f"Commande purge exécutée par {interaction.user.display_name}")
    try:
        dev_id = os.getenv("DEV_ID")
        dev_user = await logger_bot.fetch_user(dev_id)
        dm_channel = await dev_user.create_dm()
        async for message in dm_channel.history(limit=None):
            if message.created_at < discord.utils.utcnow() - datetime.timedelta(hours=48):
                await message.delete()
    except discord.HTTPException as e:
        logger.error(f"Erreur lors de la purge : {e}")
        await interaction.followup.send("Une erreur est survenue lors de la purge.", ephemeral=True)

async def auto_purge():
    try:
        dev_id = os.getenv("DEV_ID")
        dev_user = await logger_bot.fetch_user(dev_id)
        dm_channel = await dev_user.create_dm()
        async for message in dm_channel.history(limit=None):
            if message.created_at < discord.utils.utcnow() - datetime.timedelta(hours=48):
                await message.delete()
    except discord.HTTPException as e:
        logger.error(f"Erreur lors de la purge : {e}")

async def run_logger_bot():
    try:
        await logger_bot.start(LOGGER_TOKEN)
        while True:
            await auto_purge()
            await asyncio.sleep(3600)
    except discord.LoginFailure as e:
        logger.error(f"Erreur de connexion : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        await logger_bot.close()
    finally:
        logger.info("Arrêt du bot Logger.")
        raise SystemExit(0)
