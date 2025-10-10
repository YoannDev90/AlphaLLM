import discord
from discord.ext import commands
import logging
from commands.cmds import setup_commands
from utils.database import get_supabase_client
from utils.config import get_admin_bot_token, GUILD_ID, DEV_IDS, is_dev_id, LOGGER_NAME
import os
import asyncio
import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = get_admin_bot_token()

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", owner_ids=DEV_IDS, intents=intents)

supabase = get_supabase_client()
logger = logging.getLogger(LOGGER_NAME)

@bot.event
async def on_ready():
    activity = discord.CustomActivity(name="⚙️ Administrate AlphaLLM")
    await bot.change_presence(activity=activity, status=discord.Status.online)
    await bot.tree.sync()
    while True:
        await auto_purge()
        await asyncio.sleep(60)

async def auto_purge():
    try:
        # Utilise le premier développeur de la liste pour les DMs
        dev_user = await bot.fetch_user(DEV_IDS[0]) if DEV_IDS else None
        if not dev_user:
            return
        dm_channel = await dev_user.create_dm()
        
        cutoff_time = discord.utils.utcnow() - datetime.timedelta(days=2.0)
        deleted_count = 0
        
        async for message in dm_channel.history(limit=None, before=cutoff_time):
            try:
                await message.delete()
                deleted_count += 1
            except discord.NotFound:
                continue
            except discord.HTTPException:
                continue
                
    except discord.HTTPException as e:
        logger.error(f"Erreur lors de la purge : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'auto-purge : {e}")

@bot.tree.command(name="clear", description="Purge tous les messages DM sans limite de temps")
async def clear_command(interaction: discord.Interaction):
    try:
        if not is_dev_id(interaction.user.id):
            await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Utilise le premier développeur de la liste pour les DMs
        dev_user = await bot.fetch_user(DEV_IDS[0]) if DEV_IDS else None
        if not dev_user:
            await interaction.followup.send("❌ Aucun développeur configuré.", ephemeral=True)
            return
        dm_channel = await dev_user.create_dm()
        
        deleted_count = 0
        async for message in dm_channel.history(limit=None):
            try:
                await message.delete()
                deleted_count += 1
            except discord.NotFound:
                continue
            except discord.HTTPException:
                continue
        
        await interaction.followup.send(f"✅ {deleted_count} messages supprimés avec succès.", ephemeral=True)
        logger.info(f"Commande /clear exécutée : {deleted_count} messages supprimés")
        
    except discord.HTTPException as e:
        logger.error(f"Erreur lors de la purge manuelle : {e}")
        await interaction.followup.send(f"❌ Erreur lors de la purge : {e}", ephemeral=True)
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la commande /clear : {e}")
        await interaction.followup.send(f"❌ Erreur inattendue : {e}", ephemeral=True)

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