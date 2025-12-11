import logging
import logging.handlers
import queue
import requests
from colorama import Fore, Back, Style, init
from typing import Optional
import asyncio
import aiohttp
import discord
from config import CONFIG, LOGGING_LEVEL, LOGGER_NAME, GRAFANA_USER_ID, GRAFANA_API_KEY, DEV_IDS, LOGS_CHANNEL_ID

init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Formatter that adds colors to log levels."""

    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED
    }

    def format(self, record):
        level_color = self.COLORS.get(record.levelname, '')
        formatted = super().format(record)
        return f"{level_color}{formatted}{Style.RESET_ALL}"


class GrafanaLokiHandler(logging.Handler):
    """Handler that sends logs to Grafana Loki."""

    def __init__(self, loki_url: str, labels: dict, level: int = logging.INFO):
        super().__init__(level)
        self.loki_url = loki_url
        self.labels = labels

    def emit(self, record):
        try:
            labels = self.labels.copy()
            labels.update({
                "level": record.levelname,
                "logger": record.name,
                "filename": record.filename,
                "lineno": str(record.lineno),
                "funcname": record.funcName,
            })
            log_entry = {
                "streams": [
                    {
                        "stream": labels,
                        "values": [
                            [str(int(record.created * 1e9)), self.format(record)]
                        ]
                    }
                ]
            }
            requests.post(self.loki_url, auth=(GRAFANA_USER_ID, GRAFANA_API_KEY), json=log_entry, headers={"Content-Type": "application/json"})
        except Exception:
            self.handleError(record)


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
            channel = await self.bot.fetch_channel(LOGS_CHANNEL_ID)
            await channel.send(message)
        except Exception as e:
            print(f"Error sending log to channel: {e}")

    def emit(self, record):
        message = self.format(record)
        try:
            # Essayer d'obtenir la boucle d'événements en cours
            loop = asyncio.get_running_loop()
            if not self.bot.is_ready():
                return  # Ignore logs until bot is ready
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


def setup_logging(bot=None):
    """Setup logging with console, file, and custom handlers."""

    # Get config
    logs_config = CONFIG.get("logs", {})
    loki_url = logs_config.get("loki_url")

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)  # Only ERROR and above for libraries

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOGGING_LEVEL)
    console_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.handlers.RotatingFileHandler('bot.log')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Queue for async handlers
    log_queue = queue.Queue()

    # Discord handler
    if bot:
        discord_handler = DiscordLogHandler(bot)
        discord_formatter = DiscordFormatter()
        discord_handler.setFormatter(discord_formatter)
        discord_handler.setLevel(logging.INFO)
        logger.addHandler(discord_handler)

    # Grafana Loki handler (async via queue)
    if loki_url:
        loki_labels = {"job": "betallm", "host": "server"}
        loki_handler = GrafanaLokiHandler(loki_url, loki_labels, level=logging.INFO)
        loki_formatter = logging.Formatter('%(message)s')
        loki_handler.setFormatter(loki_formatter)
        queue_handler_loki = logging.handlers.QueueHandler(log_queue)
        queue_handler_loki.setLevel(logging.INFO)
        logger.addHandler(queue_handler_loki)

    # Start queue listener if any async handlers
    handlers_list = []
    if loki_url:
        handlers_list.append(loki_handler)
    if handlers_list:
        listener = logging.handlers.QueueListener(log_queue, *handlers_list)
        listener.start()

    # Set specific logger level
    bot_logger = logging.getLogger(LOGGER_NAME)
    bot_logger.setLevel(LOGGING_LEVEL)


# For async cleanup
async def close_logging():
    """Close any async resources in handlers."""
    # If DiscordWebhookHandler used session, close it
    pass  # For now, since we used requests