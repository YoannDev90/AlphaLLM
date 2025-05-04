#utils/logger_utils.py

import logging
from colorama import Fore, Back, Style
import asyncio
import os
import discord

class DiscordLogHandler(logging.Handler):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.log_queue = asyncio.Queue()
        self.running = False

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
            dev_id = os.getenv("DEV_ID")
            dev_user = await self.bot.fetch_user(dev_id)
            await dev_user.send(message)
        except discord.HTTPException as e:
            print(f"Erreur lors de la récupération de l'utilisateur : {e}")
        except Exception as e: 
            pass

    def emit(self, record):
        message = self.format(record)
        asyncio.create_task(self.log_queue.put(message))
        if not hasattr(self, 'log_task') or self.log_task is None or self.log_task.done():
            self.log_task = asyncio.create_task(self._send_logs())

    def stop(self):
        self.running = False
        asyncio.create_task(self.log_queue.put(None))

class ConsoleFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Fore.WHITE + Back.BLUE + Style.BRIGHT + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.INFO: Fore.WHITE + Back.GREEN + Style.BRIGHT + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.WARNING: Fore.WHITE + Back.YELLOW + Style.BRIGHT + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.ERROR: Fore.WHITE + Back.RED + Style.BRIGHT + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.CRITICAL: Fore.WHITE + Back.BLACK + Style.BRIGHT + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class DiscordFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: '```ansi\n[2;31m[0m[2;47m[0m[2;31m[0m[2;34m *️⃣ %(asctime)s - %(levelname)s - %(message)s [0m\n```',
        logging.INFO: '```ansi\n[2;31m[0m[2;47m[0m[2;31m[0m[2;34m[0m[2;32m ✅ %(asctime)s - %(levelname)s - %(message)s [0m\n```',
        logging.WARNING: '```ansi\n[2;31m[0m[2;47m[0m[2;31m[0m[2;34m[0m[2;32m[0m[2;33m 🚧 %(asctime)s - %(levelname)s - %(message)s [0m\n```',
        logging.ERROR: '```ansi\n[2;31m[0m[2;47m[0m[2;31m ❌ %(asctime)s - %(levelname)s - %(message)s [0m\n```',
        logging.CRITICAL: '```ansi\n[2;31m[0m[2;47m[0m[2;31m[0m[2;34m[0m[2;32m[0m[2;33m[0m[2;30m[0m[2;37m[0m[2;30m 🔳 %(asctime)s - %(levelname)s - %(message)s [0m\n```'
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

def setup_logging(logger_name, bot):
    logger = logging.getLogger(logger_name)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ConsoleFormatter())

    file_handler = logging.FileHandler('logs/logs.txt')
    file_handler.setFormatter(FileFormatter())

    discord_handler = DiscordLogHandler(bot)
    discord_handler.setFormatter(DiscordFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(discord_handler)

    return logger
