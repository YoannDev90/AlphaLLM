import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
from commands.cmds import setup_commands
from utils.ai_process import process_ai_response
from utils.database import get_blacklist
from supabase import create_client, Client, ClientOptions
import datetime

load_dotenv()

#TOKEN = os.getenv("DEV_BOT_TOKEN")
TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", owner_id=int(os.getenv("DEV_ID")), intents=intents)

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
    
@bot.tree.command(name="purge", description="Purge messages older than 48 hours in the dev DM channel")
async def purge(interaction: discord.Interaction):
    logger.info(f"Commande purge exécutée par {interaction.user.display_name}")
    try:
        user = await bot.fetch_user(interaction.user.id)
        dm_channel = await user.create_dm()
        async for message in dm_channel.history(limit=None):
            if message.created_at < discord.utils.utcnow() - datetime.timedelta(hours=48):
                await message.delete()
    except discord.HTTPException as e:
        logger.error(f"Erreur lors de la purge : {e}")
        await interaction.followup.send("Une erreur est survenue lors de la purge.", ephemeral=True)


@bot.event
async def on_ready():
    activity = discord.CustomActivity(name="🤖 Use @AlphaLLM to chat")
    await bot.change_presence(activity=activity, status=discord.Status.idle)
    await bot.tree.sync()
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if not message.author.bot:
        logger.debug(f"Message reçu de {message.author}: {message.content}")
        bot_mentioned = is_bot_mentioned(bot, message)

        if bot_mentioned:
            
            blacklist_data = get_blacklist()
                
            blacklist_entry = next((entry for entry in blacklist_data if entry.get('id_discord') == message.author.id), None)
            if blacklist_entry:
                reason = blacklist_entry.get('reason', 'Unspecified')
                logger.info(f"Message de {message.author.display_name} (ID: {message.author.id}) ignoré - Liste noire - Motif: {reason}")
                await message.channel.send(f"⛔️ You are blacklisted from the bot (<@{message.author.id}>) - Reason: **{reason}**")
                return

            await process_ai_response(bot,message)

async def run_bot():
    logger.info("Démarrage ...")
    await setup_commands(bot)
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