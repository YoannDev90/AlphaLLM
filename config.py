import json
import logging
import os
import tomllib
from pathlib import Path
from typing import Any, Dict, Iterable, Union

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def load_toml_config(file_path: str = "config.toml") -> Dict[str, Any]:
    """Charge la configuration depuis un fichier TOML"""
    with open(file_path, "rb") as f:
        return tomllib.load(f)


def read_file(file_path: Union[str, Path]) -> str:
    """Lit le contenu d'un fichier texte"""
    with open(file_path, "r", encoding="utf-8") as f:
        txt = f.read()
        return txt


CONFIG = load_toml_config()

CONFIG_SECTION: Dict[str, Any] = CONFIG.get("config")
API_SECTION: Dict[str, Any] = CONFIG.get("api")
LOGS_SECTION: Dict[str, Any] = CONFIG.get("logs")
MEMORY_SECTION: Dict[str, Any] = CONFIG.get("memory")
MODELS_SECTION: Dict[str, Any] = CONFIG.get("models")
DATABASE_SECTION: Dict[str, Any] = CONFIG.get("database")
UNIFIED_TEXT_SECTION: Dict[str, Any] = CONFIG.get("unified_text")
LIMITS_SECTION: Dict[str, Any] = CONFIG.get("limits")

LOGGING_LEVEL_STR = LOGS_SECTION.get("logging_level")
level_mapping = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

DEBUG: bool = bool(CONFIG_SECTION.get("debug"))
DEV_IDS: list[int] = CONFIG_SECTION.get("dev_ids", [])

AVAILABLE_MODELS: Iterable[str] = MODELS_SECTION.get("available_models")
_MODELS_LIST = MODELS_SECTION.get("models", [])
MODELS: Dict[str, str] = {model["name"]: model["description"] for model in _MODELS_LIST}
MODELS_OWNERS: Dict[str, str] = {
    model["name"]: model.get("owner", "") for model in _MODELS_LIST
}

LOGGING_LEVEL: int = level_mapping.get(LOGGING_LEVEL_STR.upper())
LOGGER_NAME: str = LOGS_SECTION.get("logger_name")
LOGS_CHANNEL_ID: int = LOGS_SECTION.get("channel_id")
LOGS_CATEGORY_ID: int = LOGS_SECTION.get("category_id")
LOG_ROLE_ID: int = LOGS_SECTION.get("log_role_id")
GRAFANA_USER_ID: str = LOGS_SECTION.get("user_id")
GRAFANA_API_KEY: str = os.environ.get("GRAFANA_API_KEY")
GRAFANA_URL: str = LOGS_SECTION.get("grafana_url")

API_HOST: str = API_SECTION.get("host")
API_PORT: int = API_SECTION.get("port")
API_SSL_CERTFILE: str = API_SECTION.get("ssl_certfile")
API_SSL_KEYFILE: str = API_SECTION.get("ssl_keyfile")
API_URL: str = API_SECTION.get("api_url")
API_REQUEST_TIMEOUT: int = API_SECTION.get("request_timeout")
API_KEY_REQUIRED: bool = bool(API_SECTION.get("api_key_required"))
API_KEYS_FILE: str = "data/api_keys.json"
API_KEYS: Dict[str, Dict[str, Any]] = {}
API_KEYS_MAPPING: Dict[str, str] = {}

if Path(API_KEYS_FILE).exists():
    try:
        with open(API_KEYS_FILE, "r") as f:
            API_KEYS = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load API keys: {e}")
        API_KEYS = {}

SUPPORT_SERVER: str = str(CONFIG_SECTION.get("support_server"))

EMBEDDER_MODEL: str = MEMORY_SECTION.get("embedder_model")
EMBEDDER_CACHE_DIR: str = MEMORY_SECTION.get("embedder_cache_dir")
FUNCTION_CALLING_MODEL: str = MEMORY_SECTION.get("function_calling_model")
FUNCTION_CALLING_CACHE_DIR: str = MEMORY_SECTION.get("function_calling_cache_dir")
RERANKER_MODEL: str = MEMORY_SECTION.get("reranker_model")
RERANKER_CACHE_DIR: str = MEMORY_SECTION.get("reranker_cache_dir")
STM_MAX_AGE = MEMORY_SECTION.get("stm_max_age")
LTM_MIN_SIMILARITY = MEMORY_SECTION.get("ltm_min_similarity")

BOT_TOKEN: str = (
    os.environ.get("BOT_TOKEN") if not DEBUG else os.environ.get("DEV_BOT_TOKEN")
)
ADMIN_BOT_TOKEN: str = (
    os.environ.get("ADMIN_BOT_TOKEN")
    if not DEBUG
    else os.environ.get("DEV_ADMIN_BOT_TOKEN")
)
LOGGER_BOT_TOKEN: str = os.environ.get("LOGGER_BOT_TOKEN")
ADDONS_BOTS_TOKENS_ENV_NAMES: list[str] = [
    "ADDON_1_BOT_TOKEN", "ADDON_2_BOT_TOKEN"
    ]
ADDONS_BOTS_TOKENS: list[str] = [
    os.environ.get(env_name) for env_name in ADDONS_BOTS_TOKENS_ENV_NAMES
]

OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY")
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY")
CEREBRAS_API_KEY: str = os.environ.get("CEREBRAS_API_KEY")
MEGALLM_API_KEY: str = os.environ.get("MEGALLM_API_KEY")
VOID_API_KEY: str = os.environ.get("VOID_API_KEY")
MNN_AI_API_KEY: str = os.environ.get("MNN_AI_API_KEY")
# NAGA_API_KEY: str = os.environ.get("NAGA_API_KEY")
ELECTRONHUB_API_KEY: str = os.environ.get("ELECTRONHUB_API_KEY")
AIRFORCE_API_KEY: str = os.environ.get("AIRFORCE_API_KEY")
COHERE_API_KEY: str = os.environ.get("COHERE_API_KEY")
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY")
POLLINATIONS_API_KEY: str = os.environ.get("POLLINATIONS_API_KEY")
MISTRAL_API_KEY: str = os.environ.get("MISTRAL_API_KEY")
NAVY_API_KEY: str = os.environ.get("NAVY_API_KEY")
LLM7_API_KEY: str = os.environ.get("LLM7_API_KEY")
LLM_GATEWAY_API_KEY: str = os.environ.get("LLM_GATEWAY_API_KEY")
ZANITY_API_KEY: str = os.environ.get("ZANITY_API_KEY")
ROUTEWAY_API_KEY: str = os.environ.get("ROUTEWAY_API_KEY")

HF_TOKEN: str = os.environ.get("HUGGINGFACE_TOKEN")

GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN")
GITHUB_OWNER: str = CONFIG_SECTION.get("github_owner")
GITHUB_REPO: str = CONFIG_SECTION.get("github_repo")
BUG_REPORT_CHANNEL_ID: int = CONFIG_SECTION.get("bug_report_channel_id")

IMGBB_API_KEY: str = os.environ.get("IMGBB_API_KEY")
CLOUDINARY_URL: str = os.environ.get("CLOUDINARY_URL")

SUPABASE_USER: str = os.environ.get("SUPABASE_USER")
SUPABASE_PASSWORD: str = os.environ.get("SUPABASE_PASSWORD")
SUPABASE_HOST: str = os.environ.get("SUPABASE_HOST")
SUPABASE_PORT: str = os.environ.get("SUPABASE_PORT")
SUPABASE_DBNAME: str = os.environ.get("SUPABASE_DBNAME")
SUPABASE_PG: str = (
    f"postgresql://{SUPABASE_USER}:{SUPABASE_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DBNAME}"
)
TABLES_TO_CLONE: Iterable[str] = DATABASE_SECTION.get("tables_to_clone")

PROMPT_DIR: str = UNIFIED_TEXT_SECTION.get("prompt_dir")
EVILGPT_PROMPT_PATH: Path = Path(PROMPT_DIR) / "evilgpt_prompt.txt"
API_PROMPT_PATH: Path = Path(PROMPT_DIR) / "api_prompt.txt"
STATUS_PROMPT_PATH: Path = Path(PROMPT_DIR) / "status_prompt.txt"
DISCORD_PROMPT_PATH: Path = Path(PROMPT_DIR) / "discord_prompt.txt"

MAX_STM_MESSAGES: int = LIMITS_SECTION.get("max_stm_messages", 50)
MAX_LTM_RESULTS: int = LIMITS_SECTION.get("max_ltm_results", 5)
MAX_CONVERSATION_HISTORY: int = LIMITS_SECTION.get("max_conversation_history", 10)
API_RATE_LIMIT: int = LIMITS_SECTION.get("api_rate_limit", 100)
API_BAN_THRESHOLD: int = LIMITS_SECTION.get("api_ban_threshold", 10)
DISCORD_RATE_LIMIT: int = LIMITS_SECTION.get("discord_rate_limit", 30)
