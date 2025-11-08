import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import tomllib
from utils.common.logger import setup_logging
from utils.config import DEV_IDS, is_dev_id, LOGGER_PREFIX
import asyncio
import datetime
import logging
from collections import deque

load_dotenv()

LOGGER_TOKEN = os.getenv("LOGGER_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

logger_bot = commands.Bot(command_prefix=LOGGER_PREFIX, intents=intents)
logger = setup_logging(logger_bot)

# Configuration du salon de logs
LOGS_CHANNEL_CONFIG = {
    "channel_id": None,
    "log_role_id": None,
    "channel_name": None,
    "category_id": None
}

logs_channel = None
logs_queue = deque(maxlen=100)  # Queue pour stocker les logs pendant la transition
purge_task = None
is_rotating = False  # Flag pour empêcher les double rotations


def load_logs_channel_config():
    """Charger la configuration du salon de logs depuis config.toml"""
    try:
        with open("config.toml", "rb") as f:
            config = tomllib.load(f)
        logs_config = config.get("logs_channel", {})
        LOGS_CHANNEL_CONFIG.update({
            "channel_id": logs_config.get("channel_id"),
            "log_role_id": logs_config.get("log_role_id"),
            "channel_name": logs_config.get("channel_name"),
            "category_id": logs_config.get("category_id")
        })
        logger.info(f"Logs channel config loaded: {LOGS_CHANNEL_CONFIG}")
    except Exception as e:
        logger.error(f"Error loading logs channel config: {e}")


load_logs_channel_config()


async def setup_logs_channel():
    """Initialiser la connexion au salon de logs existant"""
    global logs_channel
    if LOGS_CHANNEL_CONFIG["channel_id"]:
        logs_channel = logger_bot.get_channel(LOGS_CHANNEL_CONFIG["channel_id"])
        if logs_channel:
            logger.info(f"Logs channel connected: {logs_channel.name}")
        else:
            logger.error(f"Cannot find logs channel with ID: {LOGS_CHANNEL_CONFIG['channel_id']}")
    else:
        logger.warning("Logs channel ID not configured")


async def auto_purge():
    """Supprimer les messages du salon de logs qui ont plus de 2 jours"""
    global logs_channel
    try:
        if not logs_channel:
            return
        
        cutoff_time = discord.utils.utcnow() - datetime.timedelta(days=2.0)
        messages_to_delete = []
        
        # Collecter les messages à supprimer
        async for message in logs_channel.history(limit=None, before=cutoff_time, oldest_first=True):
            messages_to_delete.append(message)
            
            # Discord bulk delete max 100 messages
            if len(messages_to_delete) == 100:
                try:
                    await logs_channel.delete_messages(messages_to_delete)
                    logger.debug(f"Purged {len(messages_to_delete)} messages from logs channel")
                    messages_to_delete = []
                except Exception as e:
                    logger.error(f"Error during bulk delete: {e}")
        
        # Supprimer les messages restants
        if messages_to_delete:
            try:
                await logs_channel.delete_messages(messages_to_delete)
                logger.debug(f"Purged {len(messages_to_delete)} remaining messages from logs channel")
            except Exception as e:
                logger.error(f"Error during final bulk delete: {e}")
        
        logger.info(f"Auto-purge completed")
        
    except Exception as e:
        logger.error(f"Error during auto-purge: {e}")


async def purge_loop():
    """Boucle de purge automatique toutes les 6 heures"""
    try:
        while True:
            await asyncio.sleep(21600)  # 6 heures
            await auto_purge()
    except asyncio.CancelledError:
        logger.info("Purge loop cancelled")
        pass


async def flush_logs_queue():
    """Vider la queue de logs dans le nouveau salon"""
    global logs_channel
    try:
        if not logs_queue or not logs_channel:
            return
        
        # Envoyer les logs en attente
        while logs_queue:
            log_message = logs_queue.popleft()
            try:
                # Limiter à 2000 caractères pour Discord
                if len(log_message) > 2000:
                    # Envoyer en plusieurs messages
                    for i in range(0, len(log_message), 2000):
                        await logs_channel.send(log_message[i:i+2000])
                else:
                    await logs_channel.send(log_message)
            except Exception as e:
                logger.error(f"Error sending queued log: {e}")
                logs_queue.appendleft(log_message)  # Re-ajouter à la queue
                break
        
        logger.info("Logs queue flushed to new channel")
    except Exception as e:
        logger.error(f"Error flushing logs queue: {e}")


@logger_bot.event
async def on_ready():
    global logs_channel, purge_task
    activity = discord.CustomActivity(name="🎛️ Monitoring AlphaLLM")
    await logger_bot.change_presence(activity=activity)
    await logger_bot.tree.sync()
    
    # Initialiser la connexion au salon de logs
    await setup_logs_channel()
    
    # Mettre à jour la référence du logs channel dans le logger
    logger_bot._logs_channel = logs_channel
    
    # Lancer la tâche de purge automatique
    if purge_task is None or purge_task.done():
        purge_task = asyncio.create_task(purge_loop())
        logger.info("Auto-purge loop started")



@logger_bot.tree.command(name="clear-logs", description="Clear logs channel and create a new one")
async def clear_logs_command(interaction: discord.Interaction):
    """Créer un nouveau salon de logs et supprimer l'ancien"""
    global logs_channel, is_rotating
    
    try:
        if not is_dev_id(interaction.user.id):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        if is_rotating:
            await interaction.response.send_message("⏳ A rotation is already in progress. Please wait...", ephemeral=True)
            return
        
        is_rotating = True
        await interaction.response.defer(ephemeral=True)
        
        logger.info(f"/clear-logs command executed by {interaction.user.display_name}")
        
        # Récupérer le serveur admin
        admin_guild = logger_bot.get_guild(LOGS_CHANNEL_CONFIG.get("category_id")) or logger_bot.guilds[0]
        if not admin_guild:
            await interaction.followup.send("❌ Cannot find admin server.", ephemeral=True)
            is_rotating = False
            return
        
        # Récupérer les propriétés de l'ancien salon
        old_channel = logs_channel
        role_id = LOGS_CHANNEL_CONFIG.get("log_role_id")
        category_id = LOGS_CHANNEL_CONFIG.get("category_id")
        channel_name = LOGS_CHANNEL_CONFIG.get("channel_name", "📄-logs")
        
        # Chercher la catégorie
        category = None
        if category_id:
            category = admin_guild.get_channel(category_id)
        
        # Créer le nouveau salon
        try:
            overwrites = {}
            if role_id:
                role = admin_guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=False,
                        view_channel=True
                    )
            
            # Ajouter les permissions par défaut (owner peut tout faire, others rien)
            overwrites[admin_guild.default_role] = discord.PermissionOverwrite(view_channel=False)
            overwrites[admin_guild.me] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_messages=True,
                view_channel=True
            )
            
            new_channel = await admin_guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason="Logs channel rotation by /clear-logs command"
            )
            
            logger.info(f"New logs channel created: {new_channel.name} (ID: {new_channel.id})")
            logs_channel = new_channel
            
            # Mettre à jour la référence du logs channel dans le logger
            logger_bot._logs_channel = new_channel
            
            # Vider la queue des logs dans le nouveau salon
            await flush_logs_queue()
            
            # Envoyer un message d'info
            embed = discord.Embed(
                title="📝 Logs Channel Rotated",
                description=f"Old channel: {old_channel.mention if old_channel else 'Unknown'}\nNew channel: {new_channel.mention}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Executed by {interaction.user.display_name}")
            await new_channel.send(embed=embed)
            
            # Supprimer l'ancien salon avec un délai
            if old_channel:
                await asyncio.sleep(1)
                try:
                    await old_channel.delete(reason="Logs channel rotation")
                    logger.info(f"Old logs channel deleted: {old_channel.name}")
                except Exception as e:
                    logger.error(f"Error deleting old logs channel: {e}")
            
            # Mettre à jour le config.toml avec le nouvel ID
            try:
                with open("config.toml", "r") as f:
                    content = f.read()
                
                # Remplacer l'ID du salon
                import re
                content = re.sub(
                    r'channel_id = \d+',
                    f'channel_id = {new_channel.id}',
                    content
                )
                
                with open("config.toml", "w") as f:
                    f.write(content)
                
                LOGS_CHANNEL_CONFIG["channel_id"] = new_channel.id
                logger.info(f"config.toml updated with new channel ID: {new_channel.id}")
            except Exception as e:
                logger.error(f"Error updating config.toml: {e}")
            
            await interaction.followup.send(
                f"✅ Logs channel rotated successfully!\n"
                f"Old channel deleted, new channel: {new_channel.mention}",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error creating new logs channel: {e}")
            await interaction.followup.send(f"❌ Error creating new logs channel: {e}", ephemeral=True)
        
        finally:
            is_rotating = False

    except Exception as e:
        logger.error(f"Error in /clear-logs command: {e}")
        try:
            await interaction.followup.send(f"❌ Unexpected error: {e}", ephemeral=True)
        except:
            logger.error("Could not send error message - interaction expired")
        is_rotating = False


async def run_logger_bot():
    try:
        await logger_bot.start(LOGGER_TOKEN)
    except discord.LoginFailure as e:
        logger.error(f"Connection error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        if purge_task and not purge_task.done():
            purge_task.cancel()
        await logger_bot.close()
        logger.info("Logger bot stopped.")
