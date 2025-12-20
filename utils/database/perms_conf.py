import logging
from datetime import datetime

from config import LOGGER_NAME
from utils.database.db_manager import DatabaseManager

logger = logging.getLogger(LOGGER_NAME)
db_manager = DatabaseManager()

async def get_blacklist(details: bool = False):
    try:
        if details:
            blacklist = await db_manager.exc_get_query("SELECT * FROM blacklist")
        else:
            blacklist = await db_manager.exc_get_query("SELECT id_discord FROM blacklist")
        return blacklist
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la blacklist: {e}")

async def add_to_blacklist(user_id: int, reason: str):
    try:
        await db_manager.exc_modify_query(
            "INSERT INTO blacklist (id_discord, reason, datetime) VALUES (?, ?, ?)",
            (user_id, reason, datetime.now().isoformat())
        )
        logger.info(f"Utilisateur {user_id} ajouté à la blacklist pour la raison: {reason}")
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout à la blacklist: {e}")

async def remove_from_blacklist(user_id: int):
    try:
        await db_manager.exc_modify_query(
            "DELETE FROM blacklist WHERE id_discord = ?",
            (user_id,)
        )
        logger.info(f"Utilisateur {user_id} retiré de la blacklist")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la blacklist: {e}")

async def get_channel_allowed(channel_id: int) -> bool:
    try:
        result = await db_manager.exc_get_query(
            "SELECT id_channel FROM allowed_channels WHERE id_channel = ?",
            (channel_id,)
        )
        return len(result) > 0
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du canal autorisé: {e}")
        return False
    
async def get_allowed_image_gen(channel_id: int) -> bool:
    try:
        result = await db_manager.exc_get_query(
            "SELECT id_channel FROM allowed_image_gen WHERE id_channel = ?",
            (channel_id,)
        )
        return len(result) > 0
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du canal d'image autorisé: {e}")
        return False