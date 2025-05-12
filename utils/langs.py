import json
import os
import logging
from dotenv import load_dotenv
from supabase import Client, ClientOptions, create_client

load_dotenv()

logger = logging.getLogger('AlphaLLM')

url: str = os.environ.get("DB_URL", "").encode('utf-8').decode('unicode-escape') if os.environ.get("DB_URL") else None
key: str = os.environ.get("DB_KEY", "").encode('utf-8').decode('unicode-escape') if os.environ.get("DB_KEY") else None
jwt: str = os.environ.get("JWT_KEY", "").encode('utf-8').decode('unicode-escape') if os.environ.get("JWT_KEY") else None

if not url or not key or not jwt:
    raise EnvironmentError("Missing required environment variables: DB_URL, DB_KEY, or JWT_KEY")

supabase: Client = create_client(url, key, 
                                options=ClientOptions(
                                    schema="public",
                                    headers={"Authorization": f"Bearer {jwt}"},
                                    auto_refresh_token=True,
                                    persist_session=True
                                ))

def get_language(user_id):
    lang = supabase.table("users_settings").select("lang").eq("id_discord", user_id).execute()
    return lang.data[0]['lang'] if lang.data else 'EN'

def load_language(language):
    lang_path = os.path.join(os.path.dirname(__file__), '../langs', f'{language}.json')
    
    try:
        with open(lang_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Fichier de langue pour '{language}' non trouvé.")
        return None

def get_translation(language, key, **kwargs):
    translations = load_language(language)
    
    if not translations:
        return f"Traduction non trouvée pour '{key}'"
    
    keys = key.split(".")
    value = translations
    
    for k in keys:
        value = value.get(k)
        
        if value is None:
            logger.warning(f"Key '{key}' not found in translations for language '{language}'")
            return get_translation('EN', key, **kwargs)
        
    
    return value.format(**kwargs)
