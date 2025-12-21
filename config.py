import datetime
import logging
import os
import tomllib
from typing import Any, Dict, Iterable
from dotenv import load_dotenv

load_dotenv()


def load_toml_config(file_path: str = "config.toml") -> Dict[str, Any]:
    """Charge la configuration depuis un fichier TOML"""
    with open(file_path, "rb") as f:
        return tomllib.load(f)


def read_file(file_path: str) -> str:
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

LOGGING_LEVEL_STR = LOGS_SECTION.get("logging_level")
level_mapping = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

DEBUG: bool = bool(CONFIG_SECTION.get("debug"))

AVAILABLE_MODELS: Iterable[str] = MODELS_SECTION.get("available_models")
MODELS: Iterable[Dict[str, str]] = MODELS_SECTION.get("models")

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
API_KEYS: Iterable[str] = []
API_KEYS_MAPPING: Dict[str, str] = {}

SUPPORT_SERVER: str = str(CONFIG_SECTION.get("support_server"))
DEV_IDS: Iterable[int] = CONFIG_SECTION.get("dev_id")

CHROMA_DB_NAME: str = MEMORY_SECTION.get("chroma_db_name")
CHROMA_TENANT_ID: str = os.environ.get("CHROMA_TENANT_ID")
CHROMA_API_KEY: str = os.environ.get("CHROMA_API_KEY")
CHROMA_RAG_COLLECTION: str = MEMORY_SECTION.get("chroma_rag_collection")
CHROMA_STM_COLLECTION: str = MEMORY_SECTION.get("chroma_stm_collection")
CHROMA_LTM_COLLECTION: str = MEMORY_SECTION.get("chroma_ltm_collection")
EMBEDDER_MODEL: str = MEMORY_SECTION.get("embedder_model")
EMBEDDER_CACHE_DIR: str = MEMORY_SECTION.get("embedder_cache_dir")
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

OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY")
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY")
CEREBRAS_API_KEY: str = os.environ.get("CEREBRAS_API_KEY")
MEGALLM_API_KEY: str = os.environ.get("MEGALLM_API_KEY")
IO_INTELLIGENCE_API_KEY: str = os.environ.get("IO_INTELLIGENCE_API_KEY")
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

SUPABASE_USER: str = os.environ.get("SUPABASE_USER")
SUPABASE_PASSWORD: str = os.environ.get("SUPABASE_PASSWORD")
SUPABASE_HOST: str = os.environ.get("SUPABASE_HOST")
SUPABASE_PORT: str = os.environ.get("SUPABASE_PORT")
SUPABASE_DBNAME: str = os.environ.get("SUPABASE_DBNAME")
SUPABASE_PG: str = f"postgresql://{SUPABASE_USER}:{SUPABASE_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DBNAME}"
TABLES_TO_CLONE: Iterable[str] = DATABASE_SECTION.get("tables_to_clone")
