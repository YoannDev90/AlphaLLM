import importlib
import logging
import os
from pathlib import Path

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


async def setup_commands(bot, is_admin_bot=False):
    commands_dir = ["admin_commands"] if is_admin_bot else ["commands"]
    current_dir = Path(__file__).parent

    for commands_directory in commands_dir:
        directory_path = current_dir / commands_directory
        for filename in os.listdir(directory_path):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = f"bots.commands.{commands_directory}.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, "setup"):
                        await module.setup(bot)
                        logger.debug(
                            f"Commande {filename[:-3]} chargée pour {'Admin Bot' if is_admin_bot else 'Main Bot'}"
                        )
                    else:
                        logger.warning(
                            f"Le fichier {filename} n'a pas de fonction 'setup'"
                        )
                except Exception as e:
                    logger.error(f"Erreur lors du chargement de {filename}: {str(e)}")
