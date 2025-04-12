import logging
import os
from supabase import *

logger = logging.getLogger("AlphaLLM")

url: str = os.environ.get("DB_URL")
key: str = os.environ.get("DB_KEY")
jwt: str = os.environ.get("JWT_KEY")
supabase: Client = create_client(url, key, 
                                options=ClientOptions(
                                    schema="public",
                                    headers={"Authorization": f"Bearer {jwt}"},
                                    auto_refresh_token=True,
                                    persist_session=True
                                ))

def get_models():
    try:
        response = supabase.table("models").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des modèles : {str(e)}")
        return None
    
def get_blacklist():
    try:
        response = supabase.table("blacklist").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la liste noire : {str(e)}")
        return None