import logging
from utils.config.app_config import LOGGER_NAME
from colorama import Fore, Back, Style
import asyncio
import discord

logger = logging.getLogger(LOGGER_NAME)

class DiscordLogHandler(logging.Handler):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.log_queue = asyncio.Queue()
        self.running = False
        self.log_task = None
        self.logs_channel = None

    async def _send_logs(self):
        self.running = True
        while self.running:
            message = await self.log_queue.get()
            if message is None:
                break
            await self.send_channel_log(message)
            self.log_queue.task_done()

    async def send_channel_log(self, message):
        """Send logs dans le salon logs du serveur"""
        try:
            # Get logs channel depuis le bot
            if hasattr(self.bot, '_logs_channel'):
                self.logs_channel = self.bot._logs_channel
            
            # Check if channel exists et est accessible
            if not self.logs_channel:
                return
            
            try:
                # Check if channel is still accessible en tentant d'accéder à ses propriétés
                _ = self.logs_channel.id
            except (discord.NotFound, discord.Forbidden):
                # Channel no longer exists ou is not accessible
                self.logs_channel = None
                return
            
            # Discord a une limite de 2000 caractères par message
            if len(message) > 2000:
                # split le message en chunks de 2000 caractères
                for i in range(0, len(message), 2000):
                    chunk = message[i:i+2000]
                    await self.logs_channel.send(chunk)
            else:
                await self.logs_channel.send(message)
        except discord.NotFound:
            # Channel was deleted, vider la référence
            self.logs_channel = None
        except discord.Forbidden:
            # Insufficient permissions, silently ignore
            pass
        except discord.HTTPException as e:
            logger.error(f"Error sending log au salon Discord : {e}")
        except Exception as e:
            pass

    def emit(self, record):
        # Do not send DEBUG logs sur Discord
        if record.levelno == logging.DEBUG:
            return
        
        message = self.format(record)
        try:
            # Try to get event loop en cours
            loop = asyncio.get_running_loop()
            # If in a loop, create task
            asyncio.create_task(self.log_queue.put(message))
            if self.log_task is None or self.log_task.done():
                self.log_task = asyncio.create_task(self._send_logs())
        except RuntimeError:
            # No event loop running, ignorer silencieusement
            # Cela se produit quand le logging is called from non-async thread
            pass

    def stop(self):
        self.running = False
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.log_queue.put(None))
        except RuntimeError:
            pass

class ConsoleFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Fore.BLUE + Style.BRIGHT + '%(asctime)s - %(filename)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + Style.BRIGHT + '%(asctime)s - %(filename)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + Style.BRIGHT + '%(asctime)s - %(filename)s - %(funcName)s (%(lineno)d) - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.ERROR: Fore.RED + Style.BRIGHT + '%(asctime)s - %(filename)s - %(funcName)s (%(lineno)d) - %(levelname)s - %(message)s' + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class DiscordFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: '```ansi\n[2;31m[0m[2;47m[0m[2;31m[0m[2;34m *️⃣ %(asctime)s - %(message)s [0m\n```',
        logging.INFO: '```ansi\n[2;31m[0m[2;47m[0m[2;31m[0m[2;34m[0m[2;32m ✅ %(asctime)s - %(message)s [0m\n```',
        logging.WARNING: '```ansi\n[2;31m[0m[2;47m[0m[2;31m[0m[2;34m[0m[2;32m[0m[2;33m 🚧 %(asctime)s - %(message)s [0m\n```',
        logging.ERROR: '```ansi\n[2;31m[0m[2;47m[0m[2;31m ❌ %(asctime)s - %(message)s [0m\n```'
        }
    

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class FileFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: '%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
        logging.INFO: '%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
        logging.WARNING: '%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
        logging.ERROR: '%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logging(bot):
    """Centralized logging configuration"""
    logger = logging.getLogger(LOGGER_NAME)

    # Avoid handler duplication
    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ConsoleFormatter())

    file_handler = logging.FileHandler('logs.log', mode='a', encoding='utf-8')
    file_handler.setFormatter(FileFormatter())

    discord_handler = DiscordLogHandler(bot)
    discord_handler.setFormatter(DiscordFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(discord_handler)

    return logger
