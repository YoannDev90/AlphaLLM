import json
import os
import logging
from supabase import create_client, Client, ClientOptions

logger = logging.getLogger('AlphaLLM')

supabase = Client(
    os.getenv("DB_URL"),
    os.getenv("DB_KEY"),
    options=ClientOptions(headers={"Authorization": f"Bearer {os.getenv('JWT_KEY')}"})
)

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
    