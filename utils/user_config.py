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

def get_def_model(user_id):
    try:
        response = supabase.table("users_settings").select("def_model").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['def_model']
        else:
            logger.warning(f"Aucun modèle par défaut trouvé pour l'utilisateur {user_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du modèle par défaut pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_fallback_model(user_id):
    try:
        response = supabase.table("users_settings").select("fallback_model").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['fallback_model']
        else:
            logger.warning(f"Aucun modèle de secours trouvé pour l'utilisateur {user_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du modèle de secours pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_image_model(user_id):
    try:
        response = supabase.table("users_settings").select("image_model").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['image_model']
        else:
            logger.warning(f"Aucun modèle d'image trouvé pour l'utilisateur {user_id}.")
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
            logger.warning(f"Aucune taille d'image trouvée pour l'utilisateur {user_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la taille d'image pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_image_private(user_id):
    try:
        response = supabase.table("users_settings").select("image_private").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['image_private']
        else:
            logger.warning(f"Aucun statut d'image privée trouvé pour l'utilisateur {user_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut d'image privée pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_image_enhance(user_id):
    try:
        response = supabase.table("users_settings").select("image_enhance").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['image_enhance']
        else:
            logger.warning(f"Aucun statut d'amélioration d'image trouvé pour l'utilisateur {user_id}.")
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
            logger.warning(f"Aucun statut de génération audio trouvé pour l'utilisateur {user_id}.")
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
            logger.warning(f"Aucune voix trouvé pour l'utilisateur {user_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la voix pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_audio_fallback_voice(user_id):
    try:
        response = supabase.table("users_settings").select("audio_fallback").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['audio_fallback']
        else:
            logger.warning(f"Aucune voix de secours trouvé pour l'utilisateur {user_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la voix de secours pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_announce_mp_active(user_id):
    try:
        response = supabase.table("users_settings").select("announce_mp").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['announce_mp']
        else:
            logger.warning(f"Aucun statut d'annonce MP trouvé pour l'utilisateur {user_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut d'annonce MP pour l'utilisateur {user_id} : {str(e)}")
        return None
    
def get_perso_preprompt(user_id):
    try:
        response = supabase.table("users_settings").select("perso_preprompt").eq("id_discord", user_id).execute()
        if response.data:
            return response.data[0]['perso_preprompt']
        else:
            logger.warning(f"Aucun pré-prompt trouvé pour l'utilisateur {user_id}.")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du pré-prompt pour l'utilisateur {user_id} : {str(e)}")
        return None