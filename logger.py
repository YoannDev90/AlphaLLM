import asyncio
import logging
import logging.handlers
import queue
from typing import Optional

import aiohttp
import discord
import requests
from colorama import Back, Fore, Style, init
from discord import ui

from bots.logger_bot import bot
from config import (
    CONFIG,
    DEV_IDS,
    GRAFANA_API_KEY,
    GRAFANA_URL,
    GRAFANA_USER_ID,
    LOGGER_NAME,
    LOGGING_LEVEL,
    LOGS_CHANNEL_ID,
)

init(autoreset=True)
logging_components = {}


class LogButtonsView(discord.ui.View):
    def __init__(self, level, logger, timestamp):
        super().__init__(timeout=None)
        url = generate_grafana_log_url(level, logger, timestamp)
        self.add_item(
            discord.ui.Button(
                label="Grafana", url=url, emoji="📊", style=discord.ButtonStyle.link
            )
        )


EMBED_COLORS = {
    "DEBUG": 0x3498DB,
    "INFO": 0x2ECC71,
    "WARNING": 0xF39C12,
    "ERROR": 0xE74C3C,
    "CRITICAL": 0x9B59B6,
}


def generate_grafana_log_url(
    level: str, logger: str, timestamp: float, job: str = "AlphaLLM"
) -> str:
    """
    Génère l'URL Grafana Explore pour visualiser les logs correspondant.
    """
    import datetime
    import json
    from urllib.parse import urlencode

    log_time = datetime.datetime.fromtimestamp(timestamp)
    start_time = (log_time - datetime.timedelta(hours=1)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )[:-3] + "Z"
    end_time = (log_time + datetime.timedelta(hours=1)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )[:-3] + "Z"

    query = f'{{job="{job}", level="{level}", logger="{logger}"}}'
    left_panel = {
        "datasource": "loki",
        "queries": [{"refId": "A", "expr": query, "queryType": "range"}],
        "range": {"from": start_time, "to": end_time},
    }

    params = {"orgId": 1, "left": json.dumps(left_panel)}

    url = f"{GRAFANA_URL}/explore?{urlencode(params)}"
    return url


class ColoredFormatter(logging.Formatter):
    """Formatter that adds colors to log levels."""

    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Back.WHITE + Fore.BLACK,
    }

    def format(self, record):
        level_color = self.COLORS.get(record.levelname, "")
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
            labels.update(
                {
                    "level": record.levelname,
                    "logger": record.name,
                    "filename": record.filename,
                    "lineno": str(record.lineno),
                    "funcname": record.funcName,
                }
            )
            log_entry = {
                "streams": [
                    {
                        "stream": labels,
                        "values": [
                            [str(int(record.created * 1e9)), self.format(record)]
                        ],
                    }
                ]
            }
            requests.post(
                self.loki_url,
                auth=(GRAFANA_USER_ID, GRAFANA_API_KEY),
                json=log_entry,
                headers={"Content-Type": "application/json"},
            )
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
            item = await self.log_queue.get()
            if item is None:
                break
            message_text, record = item
            await self.private_channel_logs(message_text, record)
            self.log_queue.task_done()

    async def private_channel_logs(self, message_text, record):
        if self.bot.is_closed():
            return
        try:
            channel = await self.bot.fetch_channel(LOGS_CHANNEL_ID)
            ts = int(record.created)
            embed = discord.Embed(color=EMBED_COLORS.get(record.levelname, 0x95A5A6))
            embed.add_field(name="", value=f"<t:{ts}:F> (<t:{ts}:R>)", inline=False)
            embed.add_field(name="", value=f"```txt\n{message_text}\n```", inline=False)
            if record.levelno >= logging.ERROR:
                view = LogButtonsView(record.levelname, record.name, record.created)
                await channel.send(embed=embed, view=view)
            else:
                await channel.send(embed=embed)
        except Exception as e:
            pass

    def emit(self, record):
        message = self.format(record)
        if len(message) > 1000:
            import copy

            new_record = copy.copy(record)
            new_record.msg = "Log entry too long, see on Grafana: "
            message = self.format(new_record)
        try:
            loop = asyncio.get_running_loop()
            if not self.bot.is_ready() or self.bot.is_closed():
                return
            asyncio.create_task(self.log_queue.put((message, record)))
            if self.log_task is None or self.log_task.done():
                self.log_task = asyncio.create_task(self._send_logs())
        except RuntimeError:

            pass

    def stop(self):
        self.running = False
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.log_queue.put(None))
        except RuntimeError:
            pass

    def close(self):
        """Close the handler properly."""
        self.stop()


class DiscordFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: "%(message)s",
        logging.INFO: "%(message)s",
        logging.WARNING: "%(message)s",
        logging.ERROR: "%(message)s",
        logging.CRITICAL: "%(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging():
    """Setup logging with console, file, and custom handlers."""
    logs_config = CONFIG.get("logs", {})
    loki_url = logs_config.get("loki_url")

    logger = logging.getLogger()
    logger.setLevel(logging.CRITICAL)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOGGING_LEVEL)
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(levelname)s - %(filename)s : %(lineno)d - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler("data/bot.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    log_queue = queue.Queue()

    discord_handler = None
    if bot:
        discord_handler = DiscordLogHandler(bot)
        discord_formatter = DiscordFormatter()
        discord_handler.setFormatter(discord_formatter)
        discord_handler.setLevel(logging.INFO)
        logger.addHandler(discord_handler)

    queue_handler_loki = None
    if loki_url:
        loki_labels = {"job": "AlphaLLM", "host": "server"}
        loki_handler = GrafanaLokiHandler(loki_url, loki_labels, level=logging.INFO)
        loki_formatter = logging.Formatter("%(message)s")
        loki_handler.setFormatter(loki_formatter)
        queue_handler_loki = logging.handlers.QueueHandler(log_queue)
        queue_handler_loki.setLevel(logging.INFO)
        logger.addHandler(queue_handler_loki)

    handlers_list = []
    if loki_url:
        handlers_list.append(loki_handler)
    listener = None
    if handlers_list:
        listener = logging.handlers.QueueListener(log_queue, *handlers_list)
        listener.start()

    logging_components["handlers"] = [
        h
        for h in [console_handler, file_handler, discord_handler, queue_handler_loki]
        if h is not None
    ]
    logging_components["listener"] = listener

    bot_logger = logging.getLogger(LOGGER_NAME)
    bot_logger.setLevel(LOGGING_LEVEL)


def close_logging():
    """Close any async resources in handlers."""
    logger = logging.getLogger()
    for handler in logging_components.get("handlers", []):
        logger.removeHandler(handler)
        if hasattr(handler, "close"):
            handler.close()
    listener = logging_components.get("listener")
    if listener:
        listener.stop()
    logging_components.clear()
