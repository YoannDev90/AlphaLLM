import aiofiles
import json
import os
import time
import asyncio
from deep_translator import GoogleTranslator
from utils.server_config import get_guild_language
from utils.langs import get_language
import logging

logger = logging.getLogger('AlphaLLM')

CACHE_FILE = 'translation_cache.json'
CACHE_TTL = 3600
_cache_lock = asyncio.Lock()
_cache_data = None

async def _load_cache():
    global _cache_data
    async with _cache_lock:
        if _cache_data is not None:
            logger.info("Cache déjà chargé en mémoire")
            return _cache_data
        if not os.path.exists(CACHE_FILE):
            logger.info(f"Fichier de cache absent ({CACHE_FILE}), création d'un cache vide")
            _cache_data = {}
            return _cache_data
        try:
            async with aiofiles.open(CACHE_FILE, 'r') as f:
                content = await f.read()
                _cache_data = json.loads(content)
                logger.info(f"Cache chargé depuis le disque ({len(_cache_data)} entrées)")
        except Exception as e:
            logger.error(f"Erreur lecture cache traduction : {e}")
            _cache_data = {}
        return _cache_data

async def _save_cache():
    global _cache_data
    async with _cache_lock:
        try:
            async with aiofiles.open(CACHE_FILE, 'w') as f:
                await f.write(json.dumps(_cache_data))
            logger.info(f"Cache sauvegardé ({len(_cache_data)} entrées)")
        except Exception as e:
            logger.error(f"Erreur écriture cache traduction : {e}")

async def _get_or_translate(text, lang):
    logger.info(f"Requête de traduction pour la langue '{lang}' et texte : {text[:60]}...")
    cache = await _load_cache()
    cache_key = f"{lang.lower()}|{text}"
    now = int(time.time())

    if cache_key in cache:
        entry = cache[cache_key]
        if now < entry['expire_at']:
            logger.info(f"Cache HIT pour '{lang}'")
            logger.info(f"Valeur cache : {entry['value'][:60]}...")
            return entry['value']
        else:
            logger.info(f"Cache EXPIRE pour '{lang}', suppression de l'entrée")
            del cache[cache_key]
            await _save_cache()
    else:
        logger.info(f"Cache MISS pour '{lang}'")

    try:
        logger.info(f"Traduction en cours via GoogleTranslator pour '{lang}'")
        translated = await asyncio.to_thread(GoogleTranslator(source='auto', target=lang.lower()).translate, text)
        logger.info(f"Résultat traduction : {translated[:60]}...")
        if not translated:
            logger.warning(f"ATTENTION : Traduction vide pour '{lang}' et texte : {text[:60]}...")
        cache[cache_key] = {
            'value': translated,
            'expire_at': now + CACHE_TTL
        }
        await _save_cache()
        return translated
    except Exception as e:
        logger.error(f"Erreur de traduction : {e}")
        return text

async def translate_announcement_guild(text, guild):
    logger.info(f"Traduction pour guild {guild.name} (ID: {guild.id})")
    lang = get_guild_language(guild.id)
    logger.info(f"Langue détectée : {lang}")
    if not lang:
        lang = 'en'
    if lang == 'en':
        logger.info(f"Pas de traduction nécessaire (langue = 'en')")
        return text
    translated = await _get_or_translate(text, lang)
    logger.info(f"Traduction finale : {translated[:60]}...")
    return translated

async def translate_announcement_mp(text, user):
    logger.info(f"Traduction pour user {user.display_name} (ID: {user.id})")
    lang = get_language(user.id)
    logger.info(f"Langue détectée : {lang}")
    if not lang:
        lang = 'en'
    if lang == 'en':
        logger.info(f"Pas de traduction nécessaire (langue = 'en')")
        return text
    translated = await _get_or_translate(text, lang)
    logger.info(f"Traduction finale : {translated[:60]}...")
    return translated
