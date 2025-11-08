# utils/user_manager.py
import json
import logging
from utils.config.app_config import LOGGER_NAME
from utils.database.client import get_supabase_client
from datetime import datetime
from discord import Guild
from typing import List
import uuid

logger = logging.getLogger(LOGGER_NAME)
supabase = get_supabase_client()
def new_interaction(user_id: int):
    try:
        user_data = supabase.table("users").select("id").eq("id_discord", str(user_id)).execute()
        if user_data.data:
            # update activity
            supabase.table("users").update({"activity": datetime.now().isoformat()}).eq("id_discord", str(user_id)).execute()
        else:
            # insert
            supabase.table("users").insert({
                "id": str(uuid.uuid4()),
                "id_discord": str(user_id),
                "activity": datetime.now().isoformat()
            }).execute()
    except Exception as e:
        logger.error(f"Erreur mise à jour interaction : {str(e)}")
        return False
    return True

def new_image(user_id: int, count: int = 1):
    try:
        user_data = supabase.table("users").select("images").eq("id_discord", str(user_id)).execute()
        if user_data.data:
            current_images = user_data.data[0].get("images", 0)
            updated_images = current_images + count
            supabase.table("users").update({"images": updated_images}).eq("id_discord", str(user_id)).execute()
        else:
            supabase.table("users").insert({
                "id": str(uuid.uuid4()),
                "id_discord": str(user_id),
                "images": count
            }).execute()
    except Exception as e:
        logger.error(f"Erreur incrément images : {str(e)}")
        return False
    return True

def new_query(user_id: int):
    try:
        user_data = supabase.table("users").select("queries").eq("id_discord", str(user_id)).execute()
        if user_data.data:
            current_queries = user_data.data[0].get("queries", 0)
            updated_queries = current_queries + 1
            supabase.table("users").update({"queries": updated_queries}).eq("id_discord", str(user_id)).execute()
        else:
            supabase.table("users").insert({
                "id": str(uuid.uuid4()),
                "id_discord": str(user_id),
                "queries": 1
            }).execute()
    except Exception as e:
        logger.error(f"Erreur incrément requêtes : {str(e)}")
        return False
    return True