import json
import logging
from utils.config.app_config import LOGGER_NAME
from utils.database.client import get_supabase_client

logger = logging.getLogger(LOGGER_NAME)
supabase = get_supabase_client()

def get_user_language(user_id):
    try:
        response = supabase.table("users_settings").select("lang").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['lang']
        else:
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la langue pour l'utilisateur {user_id} : {str(e)}")
        return None

def get_image_model(user_id):
    try:
        response = supabase.table("users_settings").select("image_model").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['image_model']
        else:
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du modèle d'image pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_image_size(user_id):
    try:
        response = supabase.table("users_settings").select("image_size").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['image_size']
        else:
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la taille d'image pour l'utilisateur {user_id} : {str(e)}")
        return None

def get_image_private(user_id): return False

def get_image_enhance(user_id):
    try:
        response = supabase.table("users_settings").select("image_enhance").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['image_enhance']
        else:
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut d'amélioration d'image pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_audio_gen_active(user_id):
    try:
        response = supabase.table("users_settings").select("audio_gen").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['audio_gen']
        else:
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut de génération audio pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_audio_voice(user_id):
    try:
        response = supabase.table("users_settings").select("audio_voice").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['audio_voice']
        else:
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la voix pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_perso_preprompt(user_id):
    try:
        response = supabase.table("users_settings").select("perso_preprompt").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['perso_preprompt']
        else:
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du pré-prompt pour l'utilisateur {user_id} : {str(e)}")
        return None