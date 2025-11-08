import json
import os
import aiofiles
import asyncio
from typing import Dict, Optional
import logging
from utils.config.app_config import logger_name
from deep_translator import GoogleTranslator

logger = logging.getLogger(logger_name)

SUPPORTED_LANGUAGES = {
    'es': {'name': 'Español', 'emoji': '🇪🇸', 'google_code': 'es'},
    'pt': {'name': 'Português', 'emoji': '🇵🇹', 'google_code': 'pt'},
    'fr': {'name': 'Français', 'emoji': '🇫🇷', 'google_code': 'fr'},
    'de': {'name': 'Deutsch', 'emoji': '🇩🇪', 'google_code': 'de'},
    'it': {'name': 'Italiano', 'emoji': '🇮🇹', 'google_code': 'it'},
    'nl': {'name': 'Nederlands', 'emoji': '🇳🇱', 'google_code': 'nl'},
    'fi': {'name': 'Suomi', 'emoji': '🇫🇮', 'google_code': 'fi'},
    'sv': {'name': 'Svenska', 'emoji': '🇸🇪', 'google_code': 'sv'},
    'da': {'name': 'Dansk', 'emoji': '🇩🇰', 'google_code': 'da'},
    'no': {'name': 'Norsk', 'emoji': '🇳🇴', 'google_code': 'no'},
}

async def translate_text(text: str, target_language: str) -> str:
    """
    Traduit un texte vers la langue cible en utilisant Google Translate.
    """
    try:
        # Si la langue cible est l'anglais, retourner le texte original
        if target_language == 'en':
            return text
        
        # retrieve le code Google Translate pour la langue cible
        lang_info = SUPPORTED_LANGUAGES.get(target_language, {})
        google_code = lang_info.get('google_code', target_language)
        
        # create le traducteur
        translator = GoogleTranslator(source='en', target=google_code)
        
        # Exécuter la traduction dans un thread séparé pour éviter le blocage
        loop = asyncio.get_event_loop()
        translated_text = await loop.run_in_executor(
            None, 
            lambda: translator.translate(text)
        )
        
        # check that la traduction a réussi
        if translated_text and translated_text != text:
            logger.info(f"Traduction réussie en {lang_info.get('name', target_language)}")
            return translated_text
        else:
            # Fallback si la traduction échoue
            logger.warning(f"Traduction échouée pour {target_language}, utilisation du texte original")
            return text
            
    except Exception as e:
        logger.error(f"Erreur lors de la traduction en {target_language}: {e}")
        # En cas d'error, retourner le texte original
        return text

async def save_translations(file_path: str, original_message: str, translations: Dict[str, str]):
    """Sauvegarde les traductions dans un fichier JSON"""
    data = {
        'original_message': original_message,
        'translations': translations,
        'timestamp': os.path.getctime(file_path) if os.path.exists(file_path) else None
    }
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))

async def load_translations(file_path: str) -> tuple[str, Dict[str, str]]:
    """Charge les traductions depuis un fichier JSON"""
    if not os.path.exists(file_path):
        return "", {}
    
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
            return data.get('original_message', ''), data.get('translations', {})
    except Exception as e:
        logger.error(f"Erreur lors du chargement des traductions depuis {file_path}: {e}")
        return "", {}

async def generate_all_translations(original_message: str, file_path: str, progress_callback=None) -> Dict[str, str]:
    """Génère toutes les traductions pour un message donné"""
    translations = {}
    total_langs = len(SUPPORTED_LANGUAGES)
    successful_translations = 0
    failed_translations = 0
    
    logger.info(f"Début de la génération de {total_langs} traductions")
    
    for i, lang_code in enumerate(SUPPORTED_LANGUAGES.keys()):
        try:
            translated_text = await translate_text(original_message, lang_code)
            translations[lang_code] = translated_text
            successful_translations += 1
            
            if progress_callback:
                await progress_callback(i + 1, total_langs, lang_code)
            
            # Petite pause pour éviter de surcharger l'API Google
            if lang_code != 'en':  # Pas de pause pour l'anglais (pas de traduction)
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Erreur lors de la traduction en {lang_code}: {e}")
            translations[lang_code] = original_message  # Fallback au texte original
            failed_translations += 1
    
    logger.info(f"Traductions terminées - Succès: {successful_translations}, Échecs: {failed_translations}")
    
    # Sauvegarder les traductions
    await save_translations(file_path, original_message, translations)
    
    return translations

class TranslationManager:
    """Gestionnaire de traductions - conservé car utilisé dans le code existant"""
    
    def __init__(self, original_message: str, file_path: str):
        self.original_message = original_message
        self.file_path = file_path
        self.translations = {}
    
    async def load_translations(self):
        """Charge les traductions existantes"""
        self.original_message, self.translations = await load_translations(self.file_path)
    
    async def generate_all_translations(self, interaction=None):
        """Génère toutes les traductions"""
        async def progress_callback(current, total, lang_code):
            if interaction and current % 5 == 0:  # Mise à jour tous les 5 langues
                try:
                    await interaction.edit_original_response(
                        content=f"🔄 Génération des traductions... {current}/{total} ({lang_code})"
                    )
                except:
                    pass  # Ignore les erreurs de mise à jour
        
        self.translations = await generate_all_translations(
            self.original_message, self.file_path, progress_callback
        )
    
    async def get_translation(self, lang_code: str) -> str:
        """Obtient la traduction pour une langue donnée"""
        if lang_code not in self.translations:
            # Générer la traduction si elle n'existe pas
            self.translations[lang_code] = await translate_text(self.original_message, lang_code)
            # Sauvegarder la mise à jour
            await save_translations(self.file_path, self.original_message, self.translations)
        
        return self.translations[lang_code]
