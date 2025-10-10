import logging
from utils.config import LOGGER_NAME, DEV_IDS
from colorama import Fore, Back, Style
import asyncio
import discord

class DiscordLogHandler(logging.Handler):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.log_queue = asyncio.Queue()
        self.running = False
        self.log_task = None

    async def _send_logs(self):
        self.running = True
        while self.running:
            message = await self.log_queue.get()
            if message is None:
                break
            await self.mp_logs(message)
            self.log_queue.task_done()

    async def mp_logs(self, message):
        try:
            for dev_id in DEV_IDS:
                dev_user = await self.bot.fetch_user(dev_id)
                if not dev_user:
                    continue
                await dev_user.send(message)
        except discord.HTTPException as e:
            print(f"Erreur lors de la récupération de l'utilisateur : {e}")
        except Exception as e: 
            pass

    def emit(self, record):
        message = self.format(record)
        try:
            # Essayer d'obtenir la boucle d'événements en cours
            loop = asyncio.get_running_loop()
            # Si on est dans une boucle, créer la tâche
            asyncio.create_task(self.log_queue.put(message))
            if self.log_task is None or self.log_task.done():
                self.log_task = asyncio.create_task(self._send_logs())
        except RuntimeError:
            # Pas de boucle en cours, ignorer silencieusement
            # Cela se produit quand le logging est appelé depuis un thread non-async
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
        logging.DEBUG: Fore.WHITE + Back.BLUE + Style.BRIGHT + '%(asctime)s - %(filename)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.INFO: Fore.WHITE + Back.GREEN + Style.BRIGHT + '%(asctime)s - %(filename)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.WARNING: Fore.WHITE + Back.YELLOW + Style.BRIGHT + '%(asctime)s - %(filename)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.ERROR: Fore.WHITE + Back.RED + Style.BRIGHT + '%(asctime)s - %(filename)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.CRITICAL: Fore.WHITE + Back.BLACK + Style.BRIGHT + '%(asctime)s - %(filename)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
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
        logging.ERROR: '```ansi\n[2;31m[0m[2;47m[0m[2;31m ❌ %(asctime)s - %(message)s [0m\n```',
        logging.CRITICAL: '```ansi\n[2;31m[0m[2;47m[0m[2;31m[0m[2;34m[0m[2;32m[0m[2;33m[0m[2;30m[0m[2;37m[0m[2;30m 🔳 %(asctime)s - %(message)s [0m\n```'
        }
    

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class FileFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: '%(asctime)s - %(levelname)s - %(message)s',
        logging.INFO: '%(asctime)s - %(levelname)s - %(message)s',
        logging.WARNING: '%(asctime)s - %(levelname)s - %(message)s',
        logging.ERROR: '%(asctime)s - %(levelname)s - %(message)s',
        logging.CRITICAL: '%(asctime)s - %(levelname)s - %(message)s',
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logging(bot):
    """Configuration centralisée du logging"""
    logger = logging.getLogger(LOGGER_NAME)

    # Éviter la duplication des handlers
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
