"""
Configuration centralisée pour AlphaLLM
Gère les variables d'environnement et la configuration TOML
"""
import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import tomllib


load_dotenv()

def load_toml_config(file_path: str = "config.toml") -> Dict[str, Any]:
    """Charge la configuration depuis un fichier TOML"""
    with open(file_path, "rb") as f:
        return tomllib.load(f)

CONFIG = load_toml_config()

# Configuration
_config = CONFIG.get("config", {})
DEBUG = _config.get("debug", False)
LOGGER_NAME = _config.get("logger_name", "AlphaLLM")
LOGGER_PREFIX = _config.get("logger_prefix", "[=]")
GUILD_ID = int(_config.get("admin_server", 0))
DEV_IDS = _config.get("dev_id", [])
# Pour compatibilité, on garde OWNER_ID qui prend le premier ID de la liste
OWNER_ID = DEV_IDS[0] if DEV_IDS else 0

# Links
_links = CONFIG.get("links", {})
SUPPORT_SERVER = _links.get("support_server", "https://discord.gg/QGvyrUgwdK")
WEBSITE = _links.get("website", "https://www.alphallm.com")
STATUS_PAGE = _links.get("status_page", "https://alphallm.com/status")

# API Configuration
_api = CONFIG.get("api", {})
API_HOST = _api.get("host", "0.0.0.0")
API_PORT = _api.get("port", 25692)
API_URL = _api.get("url", "https://alphallm-api.onrender.com")
API_KEY_REQUIRED = _api.get("key_required", True)
MAX_REQUESTS_PER_MINUTE = _api.get("max_requests_per_minute", 60)
REQUEST_TIMEOUT = _api.get("request_timeout", 30)

API_KEYS_MAPPING = CONFIG.get("api_keys", {})
API_KEYS = set(API_KEYS_MAPPING.values())

# Memory Configuration
_memory = CONFIG.get("memory", {})
CHROMA_DB_NAME = _memory.get("chroma_db_name", "AlphaLLM")
EMBEDDER_MODEL = _memory.get("embedder_model", "BAAI/bge-small-en-v1.5")
MEMORY_DURATION = _memory.get("memory_duration", 14400)
RECENT_LIMIT = _memory.get("recent_limit", 3)
SIMILAR_LIMIT = _memory.get("similar_limit", 5)

# Configuration de logging

_level_str = CONFIG.get("logging_level", "INFO")
_level_mapping = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
LOGGING_LEVEL = _level_mapping.get(_level_str, logging.INFO)

# Preprompts
_preprompts = CONFIG.get("preprompts", {})
BASE_PREPROMPT = _preprompts.get("base_preprompt", "")
API_MODELS_PREPROMPT = _preprompts.get("api_models_preprompt", "")
IMAGE_ENHANCER_PREPROMPT = _preprompts.get("image_enhancer_preprompt", "")
BASIC_INFOS_PREPROMPT = _preprompts.get("basic_infos_preprompt", "")
LLM_SELECTOR_PREPROMPT = _preprompts.get("llm_selector_preprompt", "")

# Bots configuration
BOTS_LINKS = CONFIG.get("bots_links", {})
BOTS_IDS = CONFIG.get("bots_ids", {})

# API Endpoints
API_ENDPOINTS = CONFIG.get("api_endpoints", {})
API_ENDPOINTS_TEXT = API_ENDPOINTS.get("text", {})
API_ENDPOINTS_IMAGE = API_ENDPOINTS.get("image", {})
API_ENDPOINTS_OTHER = API_ENDPOINTS.get("other", {})

# Model Names Configuration
MODELS_CONFIG = CONFIG.get("models_config", {})
MODELS_CONFIG_TEXT = MODELS_CONFIG.get("text", {})
MODELS_CONFIG_IMAGE = MODELS_CONFIG.get("image", {})

# Timeouts
TIMEOUTS = CONFIG.get("timeouts", {})
TIMEOUT_INSTALL_VIEW = TIMEOUTS.get("install_view", 300)
TIMEOUT_UNINSTALL_VIEW = TIMEOUTS.get("uninstall_view", 60)
TIMEOUT_ANNOUNCE_CONFIRM = TIMEOUTS.get("announce_confirm", 300)
TIMEOUT_POLL_VIEW = TIMEOUTS.get("poll_view", 300)
TIMEOUT_CONFIG_VIEW = TIMEOUTS.get("config_view", 300)
TIMEOUT_IMAGE_VIEW = TIMEOUTS.get("image_view", 30)
TIMEOUT_API_REQUEST = TIMEOUTS.get("api_request", 30)

# Limits
LIMITS = CONFIG.get("limits", {})
MAX_TOKENS_IMAGE_DESCRIPTION = LIMITS.get("max_tokens_image_description", 512)

# Variables d'environnement - Tokens Discord
_BOT_TOKEN = os.getenv("BOT_TOKEN")
_DEV_BOT_TOKEN = os.getenv("DEV_BOT_TOKEN")
LOGGER_BOT_TOKEN = os.getenv("LOGGER_BOT_TOKEN")
_ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
_DEV_ADMIN_BOT_TOKEN = os.getenv("DEV_ADMIN_BOT_TOKEN")

# Base de données
DB_URL = os.getenv("DB_URL", "").encode('utf-8').decode('unicode-escape')
DB_KEY = os.getenv("DB_KEY", "").encode('utf-8').decode('unicode-escape')
JWT_KEY = os.getenv("JWT_KEY", "").encode('utf-8').decode('unicode-escape')

CHROMA_TENANT_ID = os.getenv("CHROMA_TENANT_ID", "").encode('utf-8').decode('unicode-escape')
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY", "").encode('utf-8').decode('unicode-escape')

# PostgreSQL (pour memory_ai)
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

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

# Tokens des bots (selon le mode debug)
BOT_TOKEN = _DEV_BOT_TOKEN if DEBUG else _BOT_TOKEN
ADMIN_BOT_TOKEN = _DEV_ADMIN_BOT_TOKEN if DEBUG else _ADMIN_BOT_TOKEN

# Aliases pour compatibilité avec l'ancienne version
logger_name = LOGGER_NAME
debug = DEBUG
api_host = API_HOST
api_port = API_PORT
owner_id = OWNER_ID

# Fonctions de compatibilité (retournent les constantes)
def logging_level():
    """Alias de compatibilité pour LOGGING_LEVEL"""
    return LOGGING_LEVEL

def load_preprompt():
    """Alias de compatibilité pour BASE_PREPROMPT"""
    return BASE_PREPROMPT

def load_image_enhancer_preprompt():
    """Alias de compatibilité pour IMAGE_ENHANCER_PREPROMPT"""
    return IMAGE_ENHANCER_PREPROMPT

def get_logging_level() -> int:
    """Alias de compatibilité pour LOGGING_LEVEL"""
    return LOGGING_LEVEL

def get_base_preprompt() -> str:
    """Alias de compatibilité pour BASE_PREPROMPT"""
    return BASE_PREPROMPT

def get_image_enhancer_preprompt() -> str:
    """Alias de compatibilité pour IMAGE_ENHANCER_PREPROMPT"""
    return IMAGE_ENHANCER_PREPROMPT

def get_llm_selector_preprompt() -> str:
    """Alias de compatibilité pour LLM_SELECTOR_PREPROMPT"""
    return LLM_SELECTOR_PREPROMPT

def get_bot_token() -> str:
    """Alias de compatibilité pour BOT_TOKEN"""
    return BOT_TOKEN

def get_admin_bot_token() -> str:
    """Alias de compatibilité pour ADMIN_BOT_TOKEN"""
    return ADMIN_BOT_TOKEN

def update_log_level(new_level: str) -> bool:
    config_path = "config.toml"
    
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if new_level.upper() not in valid_levels:
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('logging_level'):
                indent = line[:len(line) - len(line.lstrip())]
                comment_pos = line.find('#')
                comment = line[comment_pos:] if comment_pos != -1 else ''
                
                lines[i] = f'{indent}logging_level = "{new_level.upper()}" {comment}'.rstrip() + '\n'
                break
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
    
    except Exception as e:
        print(f"Erreur lors de la modification du fichier config.toml: {e}")
        return False


def get_current_log_level() -> Optional[str]:
    try:
        config = load_toml_config("config.toml")
        return config.get("logging_level")
    except Exception as e:
        print(f"Erreur lors de la lecture du niveau de log: {e}")
        return None

def is_dev_id(user_id: int) -> bool:
    """Vérifie si l'ID utilisateur est dans la liste des développeurs"""
    return user_id in DEV_IDS