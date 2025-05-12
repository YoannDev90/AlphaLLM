import json
import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client, ClientOptions

load_dotenv()

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