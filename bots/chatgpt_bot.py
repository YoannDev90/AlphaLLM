import discord
from discord.ext import commands
import logging
from commands.cmds import setup_commands
from utils.database import get_supabase_client
from utils.config import DEBUG, GUILD_ID, OWNER_ID, LOGGER_NAME
from utils.msg_process import message_process
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("CHATGPT_BOT_TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", owner_id=OWNER_ID, intents=intents)

supabase = get_supabase_client()
logger = logging.getLogger(LOGGER_NAME)

@bot.event
async def on_ready():
    activity = discord.CustomActivity(name="🚀 Powered by AlphaLLM")
    await bot.change_presence(activity=activity, status=discord.Status.idle)
    await bot.tree.sync()

@bot.event
async def on_message(message):
    await message_process(bot, message)

async def run_chatgpt_bot():
    try:
        await bot.start(TOKEN)
    except discord.LoginFailure as e:
        logger.error(f"Erreur de connexion : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        await bot.close()
    finally:
        logger.info("Arrêt du bot ChatGPT.")
        raise SystemExit(0)