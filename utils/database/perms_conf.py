import json
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
            blacklist = [
                {
                    "id_discord": int(row[0]),
                    "reason": row[1],
                    "datetime": datetime.fromisoformat(row[2]) if row[2] else None,
                }
                for row in blacklist
            ]
        else:
            blacklist = await db_manager.exc_get_query(
                "SELECT id_discord FROM blacklist"
            )
            blacklist = [int(row[0]) for row in blacklist]
        return blacklist
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la blacklist: {e}")


async def get_allowed_channels(server_id: int) -> list[int]:
    try:
        result = await db_manager.exc_get_query(
            "SELECT allowed_channels FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        if result and result[0][0]:
            allowed = json.loads(result[0][0])
            return [int(cid) for cid in allowed]
        return []
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des canaux autorisés: {e}")
        return []


async def get_allowed_roles(server_id: int) -> list[int]:
    try:
        result = await db_manager.exc_get_query(
            "SELECT allowed_roles FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        if result and result[0][0]:
            allowed = json.loads(result[0][0])
            return [int(rid) for rid in allowed]
        return []
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des rôles autorisés: {e}")
        return []
