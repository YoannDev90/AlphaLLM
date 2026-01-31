import json
import logging
from datetime import datetime

from config import LOGGER_NAME
from utils.database.db_manager import DatabaseManager

logger = logging.getLogger(LOGGER_NAME)
db_manager = DatabaseManager()


async def add_to_allowed_channels(server_id: int, channel_id: int):
    try:
        rows = await db_manager.exc_get_query(
            "SELECT allowed_channels FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        if rows:
            allowed = json.loads(rows[0][0]) if rows[0][0] else []
            if channel_id not in allowed:
                allowed.append(channel_id)
                await db_manager.exc_modify_query(
                    "UPDATE server_settings_new SET allowed_channels = ?, settings_update = ? WHERE server_id = ?",
                    (json.dumps(allowed), datetime.now().isoformat(), server_id),
                )
        else:
            await db_manager.exc_modify_query(
                "INSERT INTO server_settings_new (server_id, allowed_channels, settings_update) VALUES (?, ?, ?)",
                (server_id, json.dumps([channel_id]), datetime.now().isoformat()),
            )
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout aux canaux autorisés: {e}")


async def remove_from_allowed_channels(server_id: int, channel_id: int):
    try:
        rows = await db_manager.exc_get_query(
            "SELECT allowed_channels FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        if rows:
            allowed = json.loads(rows[0][0]) if rows[0][0] else []
            if channel_id in allowed:
                allowed.remove(channel_id)
                await db_manager.exc_modify_query(
                    "UPDATE server_settings_new SET allowed_channels = ?, settings_update = ? WHERE server_id = ?",
                    (json.dumps(allowed), datetime.now().isoformat(), server_id),
                )
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des canaux autorisés: {e}")


async def add_to_allowed_roles(server_id: int, role_id: int):
    try:
        rows = await db_manager.exc_get_query(
            "SELECT allowed_roles FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        if rows:
            allowed = json.loads(rows[0][0]) if rows[0][0] else []
            if role_id not in allowed:
                allowed.append(role_id)
                await db_manager.exc_modify_query(
                    "UPDATE server_settings_new SET allowed_roles = ?, settings_update = ? WHERE server_id = ?",
                    (json.dumps(allowed), datetime.now().isoformat(), server_id),
                )
        else:
            await db_manager.exc_modify_query(
                "INSERT INTO server_settings_new (server_id, allowed_roles, settings_update) VALUES (?, ?, ?)",
                (server_id, json.dumps([role_id]), datetime.now().isoformat()),
            )
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout aux rôles autorisés: {e}")


async def remove_from_allowed_roles(server_id: int, role_id: int):
    try:
        rows = await db_manager.exc_get_query(
            "SELECT allowed_roles FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        if rows:
            allowed = json.loads(rows[0][0]) if rows[0][0] else []
            if role_id in allowed:
                allowed.remove(role_id)
                await db_manager.exc_modify_query(
                    "UPDATE server_settings_new SET allowed_roles = ?, settings_update = ? WHERE server_id = ?",
                    (json.dumps(allowed), datetime.now().isoformat(), server_id),
                )
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des rôles autorisés: {e}")


async def set_language(server_id: int, language_code: str):
    try:
        rows = await db_manager.exc_get_query(
            "SELECT server_id FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        if rows:
            await db_manager.exc_modify_query(
                "UPDATE server_settings_new SET lang = ?, settings_update = ? WHERE server_id = ?",
                (language_code, datetime.now().isoformat(), server_id),
            )
        else:
            await db_manager.exc_modify_query(
                "INSERT INTO server_settings_new (server_id, lang, settings_update) VALUES (?, ?, ?)",
                (server_id, language_code, datetime.now().isoformat()),
            )
    except Exception as e:
        logger.error(f"Erreur lors de la définition de la langue: {e}")


async def get_language(server_id: int) -> str | None:
    try:
        rows = await db_manager.exc_get_query(
            "SELECT lang FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        if rows and rows[0][0]:
            return str(rows[0][0])
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la langue: {e}")
    return None


async def set_announcement_channel(server_id: int, channel_id: int):
    try:
        rows = await db_manager.exc_get_query(
            "SELECT server_id FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        if rows:
            await db_manager.exc_modify_query(
                "UPDATE server_settings_new SET announce_channel = ?, settings_update = ? WHERE server_id = ?",
                (channel_id, datetime.now().isoformat(), server_id),
            )
        else:
            await db_manager.exc_modify_query(
                "INSERT INTO server_settings_new (server_id, announce_channel, settings_update) VALUES (?, ?, ?)",
                (server_id, channel_id, datetime.now().isoformat()),
            )
    except Exception as e:
        logger.error(f"Erreur lors de la définition du canal d'annonces: {e}")


async def get_announcement_channel(server_id: int) -> int | None:
    try:
        rows = await db_manager.exc_get_query(
            "SELECT announce_channel FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        if rows and rows[0][0]:
            return int(rows[0][0])
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du canal d'annonces: {e}")
    return None


async def set_allowed_channels(server_id: int, channel_ids: list[int]):
    try:
        rows = await db_manager.exc_get_query(
            "SELECT allowed_channels FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        current = json.loads(rows[0][0]) if rows and rows[0][0] else []

        for cid in current:
            if cid not in channel_ids:
                await remove_from_allowed_channels(server_id, cid)

        for cid in channel_ids:
            if cid not in current:
                await add_to_allowed_channels(server_id, cid)

        logger.info(
            f"Canaux autorisés mis à jour pour le serveur {server_id}: {channel_ids}"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des canaux autorisés: {e}")


async def set_allowed_roles(server_id: int, role_ids: list[int]):
    try:
        rows = await db_manager.exc_get_query(
            "SELECT allowed_roles FROM server_settings_new WHERE server_id = ?",
            (server_id,),
        )
        current = json.loads(rows[0][0]) if rows and rows[0][0] else []

        for rid in current:
            if rid not in role_ids:
                await remove_from_allowed_roles(server_id, rid)

        for rid in role_ids:
            if rid not in current:
                await add_to_allowed_roles(server_id, rid)

        logger.info(
            f"Rôles autorisés mis à jour pour le serveur {server_id}: {role_ids}"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des rôles autorisés: {e}")
