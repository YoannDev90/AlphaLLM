import importlib
import logging
import os

logger = logging.getLogger('AlphaLLM')

async def setup_commands(bot):
    commands_dir = ['global_commands', 'admin_commands']
    current_dir = os.path.dirname(__file__)

    for commands_directory in commands_dir:
        directory_path = os.path.join(current_dir, commands_directory)
        for filename in os.listdir(directory_path):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = f'commands.{commands_directory}.{filename[:-3]}'
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, 'setup'):
                        await module.setup(bot)
                        logger.debug(f"Commande {filename[:-3]} chargée")
                    else:
                        logger.warning(f"Le fichier {filename} n'a pas de fonction 'setup'")
                except Exception as e:
                    logger.error(f"Erreur lors du chargement de {filename}: {str(e)}")

async def setup_addons_commands(bot):
    commands_dir = ['addons_commands', 'global_commands']
    current_dir = os.path.dirname(__file__)

    for commands_directory in commands_dir:
        directory_path = os.path.join(current_dir, commands_directory)
        for filename in os.listdir(directory_path):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = f'commands.{commands_directory}.{filename[:-3]}'
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, 'setup'):
                        await module.setup(bot)
                        logger.debug(f"Commande {filename[:-3]} chargée")
                    else:
                        logger.warning(f"Le fichier {filename} n'a pas de fonction 'setup'")
                except Exception as e:
                    logger.error(f"Erreur lors du chargement de {filename}: {str(e)}")
