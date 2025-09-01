import discord
import sys
import os
import math
import logging
from utils.config import logger_name
from utils.config import logger_name, logging_level

logger = logging.getLogger(logger_name)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bots.bot import bot as main_bot
    from bots.chatgpt_bot import bot as chatgpt_bot
    from bots.deepseek_bot import bot as deepseek_bot
    from bots.evilgpt_bot import bot as evilgpt_bot
    from bots.gemini_bot import bot as gemini_bot
    from bots.grok_bot import bot as grok_bot
    from bots.llama_bot import bot as llama_bot
    from bots.logger_bot import logger_bot
    from bots.mistral_bot import bot as mistral_bot
    from bots.perplexity_bot import bot as perplexity_bot
    from bots.qwen_bot import bot as qwen_bot
except ImportError as e:
    logger.error(f"Erreur lors de l'import des bots: {e}")

def get_bot_status(bot: discord.Client) -> dict:
    ping = round(bot.latency * 1000, 2)
    if math.isnan(ping):
        ping = 0
        state = "offline"
    elif ping > 200:
        state = "degraded"
    else:
        state = "online"
    status = {"ping": ping, "status": state}
    return status

def get_status() -> dict:
    BOTS = [
        ("AlphaLLM", main_bot),
        ("ChatGPT", chatgpt_bot),
        ("DeepSeek", deepseek_bot),
        ("EvilGPT", evilgpt_bot),
        ("Gemini", gemini_bot),
        ("Grok", grok_bot),
        ("Llama", llama_bot),
        ("Logger", logger_bot),
        ("Mistral", mistral_bot),
        ("Perplexity", perplexity_bot),
        ("Qwen", qwen_bot),
    ]
    
    status = {}
    for bot_name, bot_instance in BOTS:
        if bot_instance is not None:
            status[bot_name] = get_bot_status(bot_instance)
        else:
            status[bot_name] = {"ping": 0, "status": "offline"}
    return status