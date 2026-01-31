import asyncio
import datetime
import logging

import discord
from discord.ext import commands

from bots.commands.cmds import setup_commands
from config import ADMIN_BOT_TOKEN, DEV_IDS, LOGGER_NAME

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", owner_ids=DEV_IDS, intents=intents)
logger = logging.getLogger(LOGGER_NAME)

purge_task = None


@bot.event
async def on_ready():
    global purge_task
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    activity = discord.CustomActivity(name="⚙️ Administrate AlphaLLM")
    await bot.change_presence(activity=activity, status=discord.Status.online)
    await bot.tree.sync()
    if purge_task is None or purge_task.done():
        purge_task = asyncio.create_task(purge_loop())


async def purge_loop():
    try:
        while True:
            await auto_purge()
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass

async def auto_purge():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            dev_user = await bot.fetch_user(DEV_IDS[0]) if DEV_IDS else None
            if not dev_user:
                return
            dm_channel = await dev_user.create_dm()
            cutoff_time = discord.utils.utcnow() - datetime.timedelta(days=2.0)
            async for message in dm_channel.history(limit=None, before=cutoff_time):
                try:
                    await message.delete()
                except (discord.NotFound, discord.HTTPException):
                    continue
            break  # Success, exit retry loop
        except discord.HTTPException as e:
            if e.status == 503 and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"503 error during auto-purge, retrying in {wait_time}s (attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"HTTP error during auto-purge: {e}")
                break
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'auto-purge : {e}")
            break

@bot.tree.command(
    name="clear", description="Purge tous les messages DM sans limite de temps"
)
async def clear_command(interaction: discord.Interaction):
    try:
        if False:
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission d'utiliser cette commande.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        dev_user = await bot.fetch_user(DEV_IDS[0]) if DEV_IDS else None
        if not dev_user:
            await interaction.followup.send(
                "❌ Aucun développeur configuré.", ephemeral=True
            )
            return
        dm_channel = await dev_user.create_dm()
        deleted_count = 0
        async for message in dm_channel.history(limit=None):
            try:
                await message.delete()
                deleted_count += 1
            except (discord.NotFound, discord.HTTPException):
                continue
        await interaction.followup.send(
            f"{deleted_count} messages supprimés avec succès.", ephemeral=True
        )
        logger.info(f"Commande /clear exécutée : {deleted_count} messages supprimés")
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la commande /clear : {e}")
        await interaction.followup.send(f"Erreur inattendue : {e}", ephemeral=True)


async def close_bot(bot):
    global purge_task
    if purge_task and not purge_task.done():
        purge_task.cancel()
        try:
            await purge_task
        except asyncio.CancelledError:
            pass
    await bot.close()


async def run_admin_bot():
    await setup_commands(bot, is_admin_bot=True)
    try:
        logger.info("Starting Admin Bot")
        await bot.start(ADMIN_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Admin bot failed: {type(e).__name__}: {e}")
    finally:
        await close_bot(bot)
        logger.info("Admin Bot stopped.")
