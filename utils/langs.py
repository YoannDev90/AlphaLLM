import json
import os
import sqlite3
import logging

logger = logging.getLogger('AlphaLLM')

get_user_lang = "SELECT lang FROM users WHERE id = ?"
set_user_lang = "UPDATE users SET lang = ? WHERE id = ?"

def get_user_language(user_id):
    conn = sqlite3.connect('config/alphallm.db')
    cursor = conn.cursor()
    try:
        cursor.execute(get_user_lang, (user_id,))
        lang = cursor.fetchone()
        return lang[0] if lang else None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la langue de l'utilisateur {user_id} : {e}")
    finally:
        conn.close()

def set_user_language(user_id, lang):
    conn = sqlite3.connect('config/alphallm.db')
    cursor = conn.cursor()
    try:
        cursor.execute(set_user_lang, (lang, user_id))
    except Exception as e:
        logger.error(f"Erreur lors de la définition de la langue de l'utilisateur {user_id} : {e}")
    finally:
        conn.commit()
        conn.close()

def load_language(language):
    lang_path = os.path.join(os.path.dirname(__file__), '../langs', f'{language}.json')
    try:
        with open(lang_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Fichier de langue pour {language} non trouvé.")
        return None

def get_translation(language, key, **kwargs):
    translations = load_language(language)
    if translations:
        text = translations.get(key, "Traduction non trouvée")
        return text.format(**kwargs)
    else:
        return "Traduction non trouvée"
