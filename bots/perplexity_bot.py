import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
from cmds import setup_addons_commands

from utils.ai_process import process_ai_response
from utils.database import get_blacklist
from supabase import create_client, Client, ClientOptions

load_dotenv()

TOKEN = os.getenv("PERPLEXITY_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!",
                    owner_id=int(os.getenv("DEV_ID")),
                    intents=intents)

url: str = os.environ.get("DB_URL").encode('utf-8').decode('unicode-escape')
key: str = os.environ.get("DB_KEY").encode('utf-8').decode('unicode-escape')
jwt: str = os.environ.get("JWT_KEY").encode('utf-8').decode('unicode-escape')
supabase: Client = create_client(url, key, 
                                options=ClientOptions(
                                    schema="public",
                                    headers={"Authorization": f"Bearer {jwt}"},
                                    auto_refresh_token=True,
                                    persist_session=True
                                ))

logger = logging.getLogger("AlphaLLM")

def is_bot_mentioned(bot, message):
    if not message.guild:
        return bot.user.mentioned_in(message)
    else:
        if message.mention_everyone:
            return False
        if bot.user.mentioned_in(message):
            return True
        if message.guild.me and any(role in message.role_mentions for role in message.guild.me.roles):
            return True
        return False


@bot.event
async def on_ready():

    activity = discord.CustomActivity(name="🚀 Powered by AlphaLLM")
    await bot.change_presence(activity=activity, status=discord.Status.idle)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if not message.author.bot:
        logger.debug(f"Message reçu de {message.author}: {message.content}")
        bot_mentioned = is_bot_mentioned(bot, message)

        if bot_mentioned:
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
            await process_ai_response(bot,message)

async def run_perplexity_bot():
    await setup_addons_commands(bot)
    try:
        await bot.start(TOKEN)
    except discord.LoginFailure as e:
        logger.error(f"Erreur de connexion : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        await bot.close()
    finally:
        logger.info("Arrêt du bot Perplexity.")
        raise SystemExit(0)