"""
Configuration centralisée pour AlphaLLM
Gère les variables d'environnement et la configuration TOML
"""
import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any
import tomllib


load_dotenv()

def load_toml_config(file_path: str = "config.toml") -> Dict[str, Any]:
    """Charge la configuration depuis un fichier TOML"""
    with open(file_path, "rb") as f:
        return tomllib.load(f)

# Configuration TOML globale
CONFIG = load_toml_config()

# Configuration de base
DEBUG = CONFIG.get("debug", False)
LOGGER_NAME = CONFIG.get("logger_name", "AlphaLLM")

# Configuration API
API_HOST = CONFIG.get("host", "0.0.0.0")
API_PORT = CONFIG.get("port", 25692)
API_URL = CONFIG.get("api_url", "https://alphallm-api.onrender.com")

# Configuration de sécurité API
API_KEY_REQUIRED = CONFIG.get("api_key_required", True)
MAX_REQUESTS_PER_MINUTE = CONFIG.get("max_requests_per_minute", 60)
REQUEST_TIMEOUT = CONFIG.get("request_timeout", 30)
API_KEYS = set(CONFIG.get("api_keys", []))

# Configuration Discord
GUILD_ID = int(CONFIG.get("admin_server", 0))
OWNER_ID = int(CONFIG.get("dev_id", 0))

# Configuration mémoire
EMBEDDER_MODEL = CONFIG.get("embedder_model", "BAAI/bge-small-en-v1.5")
MEMORY_DURATION = CONFIG.get("memory_duration", 8)
RECENT_LIMIT = CONFIG.get("recent_limit", 3)
SIMILAR_LIMIT = CONFIG.get("similar_limit", 5)

# Support server
SUPPORT_SERVER = CONFIG.get("support_server", "https://discord.gg/QGvyrUgwdK")

def get_logging_level() -> int:
    """Retourne le niveau de logging configuré"""
    level_str = CONFIG.get("logging_level", "INFO")
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_mapping.get(level_str, logging.INFO)

def get_base_preprompt() -> str:
    """Retourne le preprompt de base"""
    return CONFIG.get("base_preprompt", "")

def get_image_enhancer_preprompt() -> str:
    """Retourne le preprompt pour l'amélioration d'images"""
    return CONFIG.get("image_enhancer_preprompt", "")

def get_status_messages() -> list:
    """Retourne les messages de statut"""
    return CONFIG.get("status", [])

# Variables d'environnement communes
class EnvVars:
    """Classe pour centraliser l'accès aux variables d'environnement"""
    
    # Tokens Discord
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DEV_BOT_TOKEN = os.getenv("DEV_BOT_TOKEN")
    LOGGER_BOT_TOKEN = os.getenv("LOGGER_BOT_TOKEN")
    ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
    DEV_ADMIN_BOT_TOKEN = os.getenv("DEV_ADMIN_BOT_TOKEN")

    
    # Base de données
    DB_URL = os.getenv("DB_URL", "").encode('utf-8').decode('unicode-escape')
    DB_KEY = os.getenv("DB_KEY", "").encode('utf-8').decode('unicode-escape')
    JWT_KEY = os.getenv("JWT_KEY", "").encode('utf-8').decode('unicode-escape')
    
    # PostgreSQL (pour memory_ai)
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    
    # IDs Discord
    DEV_ID = os.getenv("DEV_ID")
    GUILD_ID = os.getenv("GUILD_ID")
    
    # APIs externes
    NAVY_API_KEY = os.getenv("NAVY_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
    AIML_API_KEY = os.getenv("AIML_API_KEY")
    
    # Cloudflare
    CLOUDFLARE_WORKERS_ACCOUNT_ID = os.getenv("CLOUDFLARE_WORKERS_ACCOUNT_ID")
    CLOUDFLARE_WORKERS_API_KEY = os.getenv("CLOUDFLARE_WORKERS_API_KEY")

def get_bot_token() -> str:
    """Retourne le token du bot approprié selon le mode debug"""
    return EnvVars.DEV_BOT_TOKEN if DEBUG else EnvVars.BOT_TOKEN

def get_admin_bot_token() -> str:
    """Retourne le token du bot approprié selon le mode debug"""
    return EnvVars.DEV_ADMIN_BOT_TOKEN if DEBUG else EnvVars.ADMIN_BOT_TOKEN

# Aliases pour compatibilité avec l'ancienne version
logger_name = LOGGER_NAME
debug = DEBUG
api_host = API_HOST
api_port = API_PORT
guild_id = GUILD_ID
owner_id = OWNER_ID

def logging_level():
    return get_logging_level()

def load_preprompt():
    return get_base_preprompt()

def load_image_enhancer_preprompt():
    return get_image_enhancer_preprompt()