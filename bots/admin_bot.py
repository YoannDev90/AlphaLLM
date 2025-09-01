import discord
from discord.ext import commands
import logging
from commands.cmds import setup_commands
from utils.database import get_supabase_client
from utils.config import DEBUG, GUILD_ID, OWNER_ID, LOGGER_NAME
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("ADMIN_BOT_TOKEN")
GUILD_ID = GUILD_ID

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", owner_id=OWNER_ID, intents=intents)

supabase = get_supabase_client()
logger = logging.getLogger(LOGGER_NAME)

@bot.event
async def on_ready():
    activity = discord.CustomActivity(name="Administrate AlphaLLM", emoji="⚙️")
    await bot.change_presence(activity=activity, status=discord.Status.online)
    await bot.tree.sync()

async def run_admin_bot():
    await setup_commands(bot, is_admin_bot=True)
    try:
        await bot.start(TOKEN)
    except discord.LoginFailure as e:
        logger.error(f"Erreur de connexion : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        await bot.close()
    finally:
        logger.info("Arrêt du bot.")
        raise SystemExit(0)