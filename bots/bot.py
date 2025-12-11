import discord
from discord.ext import commands
from commands.cmds import setup_commands
from config import BOT_TOKEN, DEBUG, LOGGER_NAME, DEV_IDS
import logging
from utils.discord_utils.permission_checker import PermissionChecker
from utils.unified_manager import unified_manager, Origin, Model

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", owner_ids=DEV_IDS, intents=intents)
logger = logging.getLogger(LOGGER_NAME)

# Initialiser le vérificateur de permissions (blacklist et canaux vides pour l'instant)
permission_checker = PermissionChecker(blacklist=[], allowed_channels=[1445804368652931254])

logging.getLogger('discord.ext.commands').setLevel(logging.CRITICAL)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    activity = discord.CustomActivity(name="🤖 Try @AlphaLLM or /commands")
    await bot.change_presence(activity=activity, status=discord.Status.idle)
    await bot.tree.sync()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Collect attachments
    files = []
    if message.attachments:
        for attachment in message.attachments:
            files.append(attachment.url)  # or attachment.filename, but URL might be better for downloads
    
    async for _ in unified_manager(
        user_id=message.author.id,
        conv_id=message.channel.id,
        input=message.content,
        model=Model.LLAMA,
        files=files if files else None,
        origin=Origin.DISCORD,
        message=message,
        bot=bot,
        permission_checker=permission_checker
    ):
        pass

async def run_bot(bot):
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