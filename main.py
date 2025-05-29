import asyncio
import warnings
from bot import run_bot
from bots.logger_bot import run_logger_bot
from bots.mistral_bot import run_mistral_bot
from bots.gemini_bot import run_gemini_bot
from bots.evilgpt_bot import run_evilgpt_bot
from bots.llama_bot import run_llama_bot
from bots.chatgpt_bot import run_chatgpt_bot
from bots.claude_bot import run_claude_bot
from bots.deepseek_bot import run_deepseek_bot
from bots.grok_bot import run_grok_bot
from bots.perplexity_bot import run_perplexity_bot
from bots.phi_bot import run_phi_bot
from bots.qwen_bot import run_qwen_bot
from utils.langs import load_language
from utils.image_gen import start_image_queue, image_queue
import logging
import sys

logger = logging.getLogger("AlphaLLM")
logger.setLevel(logging.INFO)

warnings.filterwarnings("ignore", category=DeprecationWarning)

async def main():
    try:
        loop = asyncio.get_running_loop()
        start_image_queue(loop)
        
        await asyncio.gather(
            run_bot(),
            run_logger_bot(),
            run_mistral_bot(),
            run_gemini_bot(),
            run_evilgpt_bot(),
            run_llama_bot(),
            run_chatgpt_bot(),
            run_claude_bot(),
            run_deepseek_bot(),
            run_grok_bot(),
            run_perplexity_bot(),
            run_phi_bot(),
            run_qwen_bot()
        )

    except SystemExit:
        logger.info("Arrêt complet du programme.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur non gérée : {str(e)}")
    finally:
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interruption manuelle - Arrêt du programme.")
