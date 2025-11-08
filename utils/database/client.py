from supabase import create_client, Client, ClientOptions
from utils.config.app_config import DB_URL, DB_KEY, JWT_KEY
from datetime import datetime
import logging

logger = logging.getLogger("AlphaLLM")

_supabase_client: Client = None

def get_supabase_client() -> Client:

    global _supabase_client
    
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                DB_URL,
                DB_KEY,
                options=ClientOptions(
                    schema="public",
                    headers={"Authorization": f"Bearer {JWT_KEY}"},
                    auto_refresh_token=True,
                    persist_session=True
                )
            )
            logger.debug("Client Supabase initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client Supabase: {e}")
            raise
    
    return _supabase_client

supabase = get_supabase_client()

async def get_blacklist():
    try:
        client = get_supabase_client()
        response = client.table("blacklist").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la liste noire : {str(e)}")
        return None

async def blacklist_add(user_id: int, reason: str):
    try:
        client = get_supabase_client()
        data = {
            "id_discord": user_id,
            "reason": reason,
            "datetime": datetime.now().isoformat()
        }
        response = client.table("blacklist").insert(data).execute()
        return response.data
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout à la liste noire : {str(e)}")
        return None

async def blacklist_remove(user_id: int):
    try:
        client = get_supabase_client()
        response = client.table("blacklist").delete().eq("id_discord", user_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la liste noire : {str(e)}")
        return None
    
async def get_allowed_channels(guild_id):
    try:
        client = get_supabase_client()
        response = client.table("server_settings").select("forbidden_channels").eq("id_discord", guild_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des canaux autorisés : {str(e)}")
        return None
    
async def get_allowed_roles(guild_id):
    try:
        client = get_supabase_client()
        response = client.table("server_settings").select("forbidden_roles").eq("id_discord", guild_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des rôles autorisés : {str(e)}")
        return None