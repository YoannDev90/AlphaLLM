import tomllib
import os
import logging
from utils.config import logger_name
from typing import Dict, Any, Optional

logger = logging.getLogger(logger_name)

# Mapping des codes de langue vers les fichiers toml
LANGUAGE_FILES = {
    'en': 'en.toml',
    'fr': 'fr.toml',
    'es': 'es.toml',
    'de': 'de.toml',
    'it': 'it.toml',
    'pt': 'pt.toml',
    'nl': 'nl.toml',
    'ru': 'ru.toml',
    'ja': 'ja.toml',
    'ko': 'ko.toml',
    'zh': 'zh.toml',
    'ar': 'ar.toml',
    'hi': 'hi.toml',
    'id': 'id.toml',
    'pl': 'pl.toml'
}

# Langues supportées avec leurs emojis et noms
SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'emoji': '🇺🇸', 'file': 'en.toml'},
    'fr': {'name': 'Français', 'emoji': '🇫🇷', 'file': 'fr.toml'},
    'es': {'name': 'Español', 'emoji': '🇪🇸', 'file': 'es.toml'},
    'de': {'name': 'Deutsch', 'emoji': '🇩🇪', 'file': 'de.toml'},
    'it': {'name': 'Italiano', 'emoji': '🇮🇹', 'file': 'it.toml'},
    'pt': {'name': 'Português', 'emoji': '🇵🇹', 'file': 'pt.toml'},
    'nl': {'name': 'Nederlands', 'emoji': '🇳🇱', 'file': 'nl.toml'},
    'ru': {'name': 'Русский', 'emoji': '🇷🇺', 'file': 'ru.toml'},
    'ja': {'name': '日本語', 'emoji': '🇯🇵', 'file': 'ja.toml'},
    'ko': {'name': '한국어', 'emoji': '🇰🇷', 'file': 'ko.toml'},
    'zh': {'name': '中文', 'emoji': '🇨🇳', 'file': 'zh.toml'},
    'ar': {'name': 'العربية', 'emoji': '🇸🇦', 'file': 'ar.toml'},
    'hi': {'name': 'हिन्दी', 'emoji': '🇮🇳', 'file': 'hi.toml'},
    'id': {'name': 'Bahasa Indonesia', 'emoji': '🇮🇩', 'file': 'id.toml'},
    'pl': {'name': 'Polski', 'emoji': '🇵🇱', 'file': 'pl.toml'}
}

class LanguageManager:
    def __init__(self, base_path: str = "langs"):
        self.base_path = base_path
        self._translations_cache: Dict[str, Dict[str, Any]] = {}
    
    def load_language(self, lang_code: str) -> Dict[str, Any]:
        """Charge les traductions pour une langue donnée"""
        if lang_code in self._translations_cache:
            return self._translations_cache[lang_code]
        
        # Fallback vers l'anglais si la langue n'est pas trouvée
        file_name = LANGUAGE_FILES.get(lang_code, 'en.toml')
        file_path = os.path.join(self.base_path, file_name)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    translations = tomllib.load(f)
                    self._translations_cache[lang_code] = translations
                    return translations
            else:
                logger.warning(f"Fichier de langue {file_path} introuvable, utilisation de l'anglais")
                return self.load_language('en')
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {file_path}: {e}")
            if lang_code != 'en':
                return self.load_language('en')
            return {}
    
    def get_translation(self, lang_code: str, section: str, key: str, **kwargs) -> str:
        """Récupère une traduction spécifique"""
        translations = self.load_language(lang_code)
        
        try:
            text = translations[section][key]
            # Format avec les arguments fournis
            if kwargs:
                return text.format(**kwargs)
            return text
        except KeyError:
            logger.warning(f"Traduction manquante: {lang_code}.{section}.{key}")
            # Fallback vers l'anglais
            if lang_code != 'en':
                return self.get_translation('en', section, key, **kwargs)
            return f"[Missing: {section}.{key}]"
    
    def get_section(self, lang_code: str, section: str) -> Dict[str, str]:
        """Récupère une section complète de traductions"""
        translations = self.load_language(lang_code)
        return translations.get(section, {})

# Instance globale du gestionnaire de langues
language_manager = LanguageManager()
