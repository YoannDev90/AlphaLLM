import asyncio
import warnings
import json
import datetime
import sys
import os
from bots.bot import run_bot
from bots.admin_bot import run_admin_bot
from bots.logger_bot import run_logger_bot
from bots.mistral_bot import run_mistral_bot
from bots.gemini_bot import run_gemini_bot
from bots.evilgpt_bot import run_evilgpt_bot
from bots.llama_bot import run_llama_bot
from bots.chatgpt_bot import run_chatgpt_bot
from bots.deepseek_bot import run_deepseek_bot
from bots.grok_bot import run_grok_bot
from bots.perplexity_bot import run_perplexity_bot
from bots.qwen_bot import run_qwen_bot
from bots.claude_bot import run_claude_bot
from bots.phi_bot import run_phi_bot
from bots.kimi_bot import run_kimi_bot
from bots.glm_bot import run_glm_bot
from bots.command_bot import run_command_bot

from api.api import start_api_async
from api.utils.server_utils import ping_https_server
from utils.image_gen import start_image_queue
from utils.config import LOGGER_NAME, get_logging_level, API_URL
import logging

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(get_logging_level())

async def main():
    try:
        loop = asyncio.get_running_loop()
        start_image_queue(loop)
        
        await asyncio.gather(
            start_api_async(),
            ping_https_server(API_URL),
            run_bot(),
            run_admin_bot(),
            run_logger_bot(),
            run_mistral_bot(),
            run_gemini_bot(),
            run_evilgpt_bot(),
            run_llama_bot(),
            run_chatgpt_bot(),
            run_deepseek_bot(),
            run_grok_bot(),
            run_perplexity_bot(),
            run_qwen_bot(),
            run_claude_bot(),
            run_phi_bot(),
            run_kimi_bot(),
            run_glm_bot(),
            run_command_bot()
        )

    except (SystemExit, KeyboardInterrupt):
        logger.info("Arrêt complet du programme.")
    except Exception as e:
        logger.error(f"Erreur non gérée : {str(e)}")
    finally:
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if tasks:
            for task in tasks:
                task.cancel()
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage des tâches: {str(e)}")
        logger.info("Nettoyage terminé.")

if __name__ == "__main__":
    try:
        with open("stop.json", "r") as f:
            data = json.load(f)
            timestamp = datetime.datetime.fromisoformat(data["timestamp"])
            if datetime.datetime.now() - timestamp < datetime.timedelta(minutes=1):
                print("Le bot a été arrêté récemment. Redémarrage annulé.")
                sys.exit(0)
            else:
                os.remove("stop.json")
    except FileNotFoundError:
        pass

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interruption manuelle - Arrêt du programme.")
