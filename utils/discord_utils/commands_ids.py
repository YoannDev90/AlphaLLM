"""
Utilitaire pour gérer les IDs des commandes slash Discord.
Permet de récupérer automatiquement les IDs des commandes et de créer des mentions.
"""
import discord
import logging
from config import LOGGER_NAME
from typing import Dict, Optional

logger = logging.getLogger(LOGGER_NAME)

class CommandIDManager:
    def __init__(self):
        self.command_ids: Dict[str, int] = {}
        self.bot: Optional[discord.Client] = None
    
    def set_bot(self, bot: discord.Client):
        """Définit le bot pour récupérer les IDs des commandes"""
        self.bot = bot
    
    async def fetch_command_ids(self) -> Dict[str, int]:
        """
        Récupère tous les IDs des commandes slash du bot.
        Retourne un dictionnaire {nom_commande: id_commande}
        """
        if not self.bot:
            logger.error("Bot non défini dans CommandIDManager")
            return {}
        
        try:
            commands = await self.bot.tree.fetch_commands()
            
            command_ids = {}
            for command in commands:
                command_ids[command.name] = command.id
                logger.debug(f"Commande trouvée: {command.name} (ID: {command.id})")
            
            self.command_ids = command_ids
            return command_ids
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des IDs des commandes: {e}")
            return {}
    
    def get_command_mention(self, command_name: str, subcommand: str = None, subcommand_group: str = None) -> str:
        """
        Crée une mention de commande slash Discord.
        
        Args:
            command_name: Nom de la commande principale
            subcommand: Nom de la sous-commande (optionnel)
            subcommand_group: Nom du groupe de sous-commandes (optionnel)
        
        Returns:
            Mention formatée pour Discord (ex: </ask:123456789>)
        """
        command_id = self.command_ids.get(command_name)
        
        if command_id is None:
            # Si l'ID n'est pas trouvé, retourner une mention générique
            logger.warning(f"ID de commande non trouvé pour: {command_name}")
            if subcommand_group and subcommand:
                return f"</{command_name} {subcommand_group} {subcommand}:0>"
            elif subcommand:
                return f"</{command_name} {subcommand}:0>"
            else:
                return f"</{command_name}:0>"
        
        # Construire la mention avec l'ID réel
        if subcommand_group and subcommand:
            return f"</{command_name} {subcommand_group} {subcommand}:{command_id}>"
        elif subcommand:
            return f"</{command_name} {subcommand}:{command_id}>"
        else:
            return f"</{command_name}:{command_id}>"
    
    def update_command_id(self, command_name: str, command_id: int):
        """Met à jour l'ID d'une commande spécifique"""
        self.command_ids[command_name] = command_id
        logger.debug(f"ID de commande mis à jour: {command_name} -> {command_id}")
    
    def get_all_command_ids(self) -> Dict[str, int]:
        """Retourne tous les IDs de commandes stockés"""
        return self.command_ids.copy()
    
    def has_command_id(self, command_name: str) -> bool:
        """Vérifie si l'ID d'une commande est disponible"""
        return command_name in self.command_ids

# Instance globale du gestionnaire
command_id_manager = CommandIDManager()