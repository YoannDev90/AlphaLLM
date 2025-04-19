import json
import os
import logging
from supabase import Client, ClientOptions

logger = logging.getLogger('AlphaLLM')

supabase = Client(
    os.getenv("DB_URL"),
    os.getenv("DB_KEY"),
    options=ClientOptions(headers={"Authorization": f"Bearer {os.getenv('JWT_KEY')}"})
)

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
