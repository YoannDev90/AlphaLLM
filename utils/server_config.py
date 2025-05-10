import json
import os
import logging
from supabase import create_client, Client, ClientOptions

logger = logging.getLogger('AlphaLLM')

url: str = os.environ.get("DB_URL").encode('utf-8').decode('unicode-escape')
key: str = os.environ.get("DB_KEY").encode('utf-8').decode('unicode-escape')
jwt: str = os.environ.get("JWT_KEY").encode('utf-8').decode('unicode-escape')
supabase: Client = create_client(url, key, 
                                options=ClientOptions(
                                    schema="public",
                                    headers={"Authorization": f"Bearer {jwt}"},
                                    auto_refresh_token=True,
                                    persist_session=True
                                ))

def get_announce_channel(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['announce_channel']
        else:
            logger.warning(f"Aucun salon d'annonces pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du salon d'annonces pour {server_id} : {str(e)}")
        return None
    
def get_allow_nsfw(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['allow_nsfw']
        else:
            logger.warning(f"Aucun paramètre de NSFW pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du paramètre NSFW pour {server_id} : {str(e)}")
        return None
    
def get_guild_language(server_id):
    try:
        response = supabase.table("server_settings").select("").eq("id_discord", server_id).execute()
        if response.data:
            return response.data[0]['lang']
        else:
            logger.warning(f"Aucun paramètre de langue pour le serveur {server_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du paramètre de langue pour {server_id} : {str(e)}")
        return None