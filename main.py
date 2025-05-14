import asyncio
import warnings
from bot import run_bot
from logger_bot import run_logger_bot
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
            run_logger_bot()
        )
    except SystemExit:
        logger.info("Arrêt complet du programme.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur non gérée : {str(e)}")
    finally:
        # Nettoyage des tâches
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interruption manuelle - Arrêt du programme.")
