import os
import importlib
import logging

logger = logging.getLogger('AlphaLLM')

async def setup_commands(bot):
    #commands_dir = ['commands', 'admin_commands']
    commands_dir = ['commands']
    for command in bot.commands:
        bot.remove_command(command.name)
        
    for commands_directory in commands_dir:
        for filename in os.listdir(commands_directory):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = f'{commands_directory}.{filename[:-3]}'
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, 'setup'):
                        await module.setup(bot)
                        logger.info(f"Commande {filename[:-3]} chargée")
                    else:
                        logger.warning(f"Le fichier {filename} n'a pas de fonction 'setup'")
                except Exception as e:
                    logger.error(f"Erreur lors du chargement de {filename}: {e}")
                    logger.exception(e)