#!/usr/bin/env python3

import os
import re

# Template pour les bots
BOT_TEMPLATE = """import discord
from discord.ext import commands
import logging
from commands.cmds import setup_commands
from utils.database import get_supabase_client
from utils.config import DEBUG, GUILD_ID, OWNER_ID, LOGGER_NAME
from utils.msg_process import message_process
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("{token_name}")
GUILD_ID = GUILD_ID

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

async def run_{bot_name}_bot():
    try:
        await bot.start(TOKEN)
    except discord.LoginFailure as e:
        logger.error(f"Erreur de connexion : {{e}}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {{e}}")
        await bot.close()
    finally:
        logger.info("Arrêt du bot {bot_title}.")
        raise SystemExit(0)
"""

# Mapping des bots
bots = [
    ("mistral_bot.py", "MISTRAL_BOT_TOKEN", "mistral", "Mistral"),
    ("perplexity_bot.py", "PERPLEXITY_BOT_TOKEN", "perplexity", "Perplexity"),
    ("qwen_bot.py", "QWEN_BOT_TOKEN", "qwen", "Qwen"),
    ("logger_bot.py", "LOGGER_BOT_TOKEN", "logger", "Logger")
]

def fix_bot(filename, token_name, bot_name, bot_title):
    filepath = f"/home/yoann/Documents/GitHub/AlphaLLM/bots/{filename}"
    
    # Générer le contenu du bot avec le template
    content = BOT_TEMPLATE.format(
        token_name=token_name,
        bot_name=bot_name,
        bot_title=bot_title
    )
    
    # Écrire le fichier
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {filename}")

# Fixer tous les bots
for bot_info in bots:
    fix_bot(*bot_info)

print("🎉 Tous les bots ont été standardisés !")
