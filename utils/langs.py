import json
import os

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
