from utils.database.db_manager import DatabaseManager
import logging
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
db_manager = DatabaseManager()

logger.info(f"perms_conf db_manager id: {id(db_manager)}")

async def get_blacklist(details: bool = False):
    try:
        logger.info(f"perms_conf db_manager id: {id(db_manager)}")
        logger.info("Calling get_blacklist")
        if details:
            blacklist = await db_manager.exc_get_query("SELECT * FROM blacklist")
        else:
            blacklist = await db_manager.exc_get_query("SELECT id_discord FROM blacklist")
        logger.info(f"get_blacklist returned: {blacklist}")
        return blacklist
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la blacklist: {e}")

async def add_to_blacklist(user_id: int, reason: str):
    try:
        logger.info(f"Calling add_to_blacklist for {user_id}")
        from datetime import datetime
        await db_manager.exc_modify_query(
            "INSERT INTO blacklist (id_discord, reason, datetime) VALUES (?, ?, ?)",
            (user_id, reason, datetime.now().isoformat())
        )
        logger.info(f"Utilisateur {user_id} ajouté à la blacklist pour la raison: {reason}")
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout à la blacklist: {e}")

async def remove_from_blacklist(user_id: int):
    try:
        logger.info(f"Calling remove_from_blacklist for {user_id}")
        await db_manager.exc_modify_query(
            "DELETE FROM blacklist WHERE id_discord = ?",
            (user_id,)
        )
        logger.info(f"Utilisateur {user_id} retiré de la blacklist")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la blacklist: {e}")