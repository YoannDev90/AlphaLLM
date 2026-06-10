"""Entrypoint for AlphaLLM application.

Sets up logging and starts the bot when executed as a script.
"""

import logging
import sys

from core.config import logging_cfg
from utils.logger import get_logger, setup_logging

setup_logging(
    level=getattr(logging, str(logging_cfg.level).upper(), logging.INFO),
    config=logging_cfg,
)
logger = get_logger()

if __name__ == "__main__":
    try:
        # Import bot after logging setup to capture startup logs during module import.
        import bot

        logger.info("Démarrage de l'application AlphaLLM...")
        bot.run_bot()
    except KeyboardInterrupt:
        print("\n")  # New line for cleaner exit
        logger.info("Arrêt demandé par l'utilisateur (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        logger.error("Erreur fatale: %s", e, exc_info=True)
        sys.exit(1)
