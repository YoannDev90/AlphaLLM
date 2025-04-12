import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
from cmds import setup_commands
from utils.ai_process import process_ai_response
from utils.database import get_blacklist
from utils.langs import get_translation as tlt
from datetime import datetime, timedelta


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
PREFIX = os.getenv("BOT_PREFIX")

intents = discord.Intents.all()
intents.presences = True

bot = commands.Bot(command_prefix=PREFIX,
                    owner_id=int(os.getenv("DEV_ID")),
                    intents=intents)
logger = logging.getLogger("AlphaLLM")

@bot.event
async def on_ready():
    logger.info(f'{bot.user} connecté !')
    activity = discord.CustomActivity(name="🌍 @AlphaLLM")
    await bot.change_presence(activity=activity, status=discord.Status.idle)
    logger.info("Statut mis à jour")
    logger.info("Synchronisation des commandes...")
    await bot.tree.sync()
    
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return
    try:
        blacklist_data = get_blacklist()
        
        if any(entry.get('id_discord') == message.author.id for entry in blacklist_data):
            logger.info(f"Message de {message.author} (ID: {message.author.id}) ignoré - Liste noire")
            
            try:
                await message.author.send("Vous êtes sur liste noire et ne pouvez pas interagir avec le bot.")
            except discord.Forbidden:
                logger.warning(f"Impossible de DM l'utilisateur {message.author.id}")
                await message.channel.send("Vous êtes sur liste noire et ne pouvez pas interagir avec le bot.")
            return

    except Exception as e:
        logger.error(f"Erreur vérification liste noire : {str(e)}")
        await message.channel.send("Erreur système - Veuillez réessayer plus tard", delete_after=10)
        return
    if not message.author.bot and message.channel.type == discord.ChannelType.text:
        logger.debug(f"Message reçu de {message.author}: {message.content}")
        bot_mentioned = (
            bot.user.mentioned_in(message)
            or any(role in message.role_mentions for role in message.guild.me.roles)
        )

        if bot_mentioned:
            await process_ai_response(message)

async def run_bot():
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
    finally:
        logger.info("Arrêt du bot.")
        raise SystemExit(0)