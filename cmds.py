import importlib
import logging
import os

logger = logging.getLogger('AlphaLLM')

async def setup_commands(bot):
    """
    Charge dynamiquement les commandes depuis plusieurs répertoires.
    """
    commands_dir = ['commands', 'admin_commands']
    
    for commands_directory in commands_dir:
        for filename in os.listdir(commands_directory):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = f'{commands_directory}.{filename[:-3]}'
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, 'setup'):
                        await module.setup(bot)
                        logger.debug(f"Commande {filename[:-3]} chargée")
                    else:
                        logger.warning(f"Le fichier {filename} n'a pas de fonction 'setup'")
                except Exception as e:
                    logger.error(f"Erreur lors du chargement de {filename}: {str(e)}")
