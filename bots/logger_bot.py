import asyncio
import datetime
import tomllib
from collections import deque
import discord
from discord.ext import commands
from config import LOGGER_NAME, LOGGER_BOT_TOKEN
import logging
import config

intents = discord.Intents.default()
intents.message_content = True

logger_bot = commands.Bot(command_prefix="", intents=intents)
logger = logging.getLogger(LOGGER_NAME)

LOGS_CHANNEL_CONFIG = {
    "channel_id": None,
    "log_role_id": None,
    "channel_name": None,
    "category_id": None
}

logs_channel = None
logs_queue = deque(maxlen=100)
purge_task = None
is_rotating = False


def load_logs_channel_config():
    """Charger la configuration du salon de logs depuis config.toml"""
    try:
        with open("config.toml", "rb") as f:
            config = tomllib.load(f)
        logs_config = config.get("logs", {})
        LOGS_CHANNEL_CONFIG.update({
            "channel_id": logs_config.get("channel_id"),
            "log_role_id": logs_config.get("log_role_id"),
            "channel_name": logs_config.get("channel_name"),
            "category_id": logs_config.get("category_id")
        })
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
        
        async for message in logs_channel.history(limit=None, before=cutoff_time, oldest_first=True):
            messages_to_delete.append(message)
            
            if len(messages_to_delete) == 100:
                try:
                    await logs_channel.delete_messages(messages_to_delete)
                    logger.debug(f"Purged {len(messages_to_delete)} messages from logs channel")
                    messages_to_delete = []
                except Exception as e:
                    logger.error(f"Error during bulk delete: {e}")
        
        if messages_to_delete:
            try:
                await logs_channel.delete_messages(messages_to_delete)
                logger.debug(f"Purged {len(messages_to_delete)} remaining messages from logs channel")
            except Exception as e:
                logger.error(f"Error during final bulk delete: {e}")
                
    except Exception as e:
        logger.error(f"Error during auto-purge: {e}")


async def purge_loop():
    """Boucle de purge automatique toutes les 6 heures"""
    try:
        while True:
            await asyncio.sleep(21600)
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
        
        while logs_queue:
            log_message = logs_queue.popleft()
            try:
                if len(log_message) > 2000:
                    for i in range(0, len(log_message), 2000):
                        await logs_channel.send(log_message[i:i+2000])
                else:
                    await logs_channel.send(log_message)
            except Exception as e:
                logger.error(f"Error sending queued log: {e}")
                logs_queue.appendleft(log_message)
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
    
    await setup_logs_channel()
    
    logger_bot._logs_channel = logs_channel
    
    if purge_task is None or purge_task.done():
        purge_task = asyncio.create_task(purge_loop())

@logger_bot.tree.command(name="clear-logs", description="Clear logs channel and create a new one")
async def clear_logs_command(interaction: discord.Interaction):
    """Créer un nouveau salon de logs et supprimer l'ancien"""
    global logs_channel, is_rotating
    
    try:
        if is_rotating:
            return
        
        is_rotating = True
        
        import logging
        root_logger = logging.getLogger()
        discord_handler = None
        for handler in root_logger.handlers:
            if hasattr(handler, 'bot'):
                discord_handler = handler
                original_level = handler.level
                handler.setLevel(logging.CRITICAL)
                break
        
        admin_guild = logger_bot.get_guild(LOGS_CHANNEL_CONFIG.get("category_id")) or logger_bot.guilds[0]
        if not admin_guild:
            is_rotating = False
            return
        
        old_channel = logs_channel
        role_id = LOGS_CHANNEL_CONFIG.get("log_role_id")
        category_id = LOGS_CHANNEL_CONFIG.get("category_id")
        channel_name = LOGS_CHANNEL_CONFIG.get("channel_name", "📄-logs")
        
        category = None
        if category_id:
            category = admin_guild.get_channel(category_id)
        
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
            
            logger_bot._logs_channel = new_channel
            
            await flush_logs_queue()
            
            if old_channel:
                await asyncio.sleep(1)
                try:
                    await old_channel.delete(reason="Logs channel rotation")
                    logger.info(f"Old logs channel deleted: {old_channel.name}")
                except Exception as e:
                    logger.error(f"Error deleting old logs channel: {e}")
            
            try:
                with open("config.toml", "r") as f:
                    content = f.read()
                
                import re
                content = re.sub(
                    r'channel_id = \d+',
                    f'channel_id = {new_channel.id}',
                    content
                )
                
                with open("config.toml", "w") as f:
                    f.write(content)
                
                LOGS_CHANNEL_CONFIG["channel_id"] = new_channel.id
                config.LOGS_CHANNEL_ID = new_channel.id
                logger.info(f"config.toml updated with new channel ID: {new_channel.id}")
            except Exception as e:
                logger.error(f"Error updating config.toml: {e}")
            
        except Exception as e:
            logger.error(f"Error creating new logs channel: {e}")
        
        finally:
            is_rotating = False
            if discord_handler:
                discord_handler.setLevel(original_level)
    
    except Exception as e:
        logger.error(f"Error in /clear-logs command: {e}")
        is_rotating = False


async def run_logger_bot():
    try:
        await logger_bot.start(LOGGER_BOT_TOKEN)
    except discord.LoginFailure as e:
        logger.error(f"Connection error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        if purge_task and not purge_task.done():
            purge_task.cancel()
        await logger_bot.close()
        logger.info("Logger bot stopped.")
