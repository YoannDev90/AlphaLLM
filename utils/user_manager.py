# utils/database.py
import json
import os
import logging
from datetime import datetime
from supabase import create_client, Client, ClientOptions
from discord import Guild
from typing import List

logger = logging.getLogger('AlphaLLM')

supabase = Client(
    os.getenv("DB_URL"),
    os.getenv("DB_KEY"),
    options=ClientOptions(headers={"Authorization": f"Bearer {os.getenv('JWT_KEY')}"})
)

def new_interaction(user_id: int):
    try:
        supabase.table("users").upsert({
            "id_discord": str(user_id),
            "activity": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Erreur mise à jour interaction : {str(e)}")
        return False
    return True

def new_image(user_id: int, count: int = 1):
    try:
        # Incrémentation du champ "images"
        user_data = supabase.table("users").select("images").eq("id_discord", str(user_id)).execute()
        if user_data.data:
            current_images = user_data.data[0].get("images", 0)
            updated_images = current_images + count
            supabase.table("users").update({"images": updated_images}).eq("id_discord", str(user_id)).execute()
        else:
            # Si l'utilisateur n'existe pas, insérer une nouvelle entrée
            supabase.table("users").insert({
                "id_discord": str(user_id),
                "images": count
            }).execute()
    except Exception as e:
        logger.error(f"Erreur incrément images : {str(e)}")
        return False
    return True

def new_query(user_id: int):
    try:
        # Incrémentation du champ "queries"
        user_data = supabase.table("users").select("queries").eq("id_discord", str(user_id)).execute()
        if user_data.data:
            current_queries = user_data.data[0].get("queries", 0)
            updated_queries = current_queries + 1
            supabase.table("users").update({"queries": updated_queries}).eq("id_discord", str(user_id)).execute()
        else:
            # Si l'utilisateur n'existe pas, insérer une nouvelle entrée
            supabase.table("users").insert({
                "id_discord": str(user_id),
                "queries": 1
            }).execute()
    except Exception as e:
        logger.error(f"Erreur incrément requêtes : {str(e)}")
        return False
    return True


async def set_guilds(user_id: int, bot_guilds: List[Guild]):
    try:
        # Récupération des données existantes
        existing_data = supabase.table("users").select("guilds").eq("id_discord", str(user_id)).execute()
        old_guilds = existing_data.data[0].get('guilds', []) if existing_data.data else []

        # Collecte des nouvelles données
        new_guilds = []
        for guild in bot_guilds:
            if member := guild.get_member(user_id):
                new_guild = {
                    "id": str(guild.id),
                    "pseudo": member.display_name,
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None
                }
                new_guilds.append(new_guild)

        # Conversion pour comparaison
        def process_guilds(g_list):
            return sorted([(g['id'], g['pseudo']) for g in g_list])

        # Vérification des changements
        if process_guilds(old_guilds) == process_guilds(new_guilds):
            logger.debug(f"Aucun changement pour {user_id}")
            return True

        # Mise à jour si nécessaire
        supabase.table("users").upsert({
            "id_discord": str(user_id),
            "guilds": new_guilds
        }).execute()
        logger.info(f"Mise à jour guildes pour {user_id}")

    except Exception as e:
        logger.error(f"Erreur mise à jour guildes : {str(e)}")
        return False
    return True
