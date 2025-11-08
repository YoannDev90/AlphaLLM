"""Centralized constants for all modules.

This module contains all hardcoded constants extracted from various modules
to provide a single source of truth for configuration values.

Constants are organized by domain for easy navigation and maintenance.
"""

# DISCORD API CONSTANTS

# Discord API version
DISCORD_API_VERSION = "v10"

# Discord message size constraints
MAX_MESSAGE_LENGTH = 2000

# AUDIO PROCESSING CONSTANTS

# Opus codec settings for Discord streaming
OPUS_BITRATE = "128k"
OPUS_SAMPLE_RATE = "48000"
OPUS_FORMAT = "ogg"

# Minimum samples required for waveform generation
# (for 48kHz sample rate: 480000 samples ≈ 10 seconds)
WAVEFORM_MIN_SAMPLES = 480000

# SPEECH SYNTHESIS CONSTANTS

# Text-to-speech API configuration
VOICE_API_URL = "https://text.pollinations.ai"
VOICE_UPLOAD_TIMEOUT = 300  # seconds

# Available voices for speech synthesis
AVAILABLE_VOICES = [
    "alloy",    # 0
    "echo",     # 1
    "fable",    # 2
    "onyx",     # 3
    "nova",     # 4
    "shimmer",  # 5
    "coral",    # 6
    "verse",    # 7
    "ballad",   # 8
    "ash",      # 9
    "sage",     # 10
    "amuch",    # 11
    "dan"       # 12
]

# Voice priority groups for fallback strategy
VOICE_PRIORITY_1 = AVAILABLE_VOICES[:6]   # First choice voices
VOICE_PRIORITY_2 = AVAILABLE_VOICES[6:]   # Fallback voices

# Default voice to use
DEFAULT_VOICE = "nova"

# CONTENT MODERATION CONSTANTS

# Content moderation API configuration
MODERATION_API_URL = "https://api.naga.ac/v1/moderations"
MODERATION_MODEL = "omni-moderation-latest"
MODERATION_TIMEOUT = 10  # seconds

# LLM ROUTING CONSTANTS

# Available LLM model names for routing
AVAILABLE_MODELS = [
    "mistral",
    "deepseek",
    "gemini",
    "qwen",
    "openai",
    "chatgpt",
    "evilgpt",
    "grok",
    "llama",
    "perplexity",
    "claude",
    "cohere",
    "Command",
    "glm",
    "kimi",
    "phi"
]

# Default model if selection fails
DEFAULT_MODEL = "llama"

# LLM SELECTOR ENDPOINTS

# Cascading fallback chain for LLM model selection
# Tried in order: OpenRouter → HackClub → IO Intelligence
SELECTOR_ENDPOINTS = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "openai/gpt-oss-20b"
    },
    "hackclub": {
        "url": "https://ai.hackclub.com/chat/completions",
        "model": "openai/gpt-oss-20b"
    },
    "io_intelligence": {
        "url": "https://api.intelligence.io.solutions/api/v1/chat/completions",
        "model": "openai/gpt-oss-20b"
    }
}

# LLM selection API timeout
LLM_SELECTOR_TIMEOUT = 10  # seconds

# IMAGE GENERATION CONSTANTS

# Default image generation model fallback chain
# Tried in order when main model fails
DEFAULT_FALLBACK_CHAIN = [
    "pollinations",
    "replicate",
    "huggingface"
]

# Image edit/modification model fallback chain
EDIT_FALLBACK_CHAIN = [
    "replicate-edit",
    "huggingface-edit",
    "pollinations-edit"
]

# Image generation API timeouts
IMAGE_GENERATION_TIMEOUT = 60  # seconds
IMAGE_EDIT_TIMEOUT = 60  # seconds

# Maximum image generation retries
MAX_IMAGE_RETRIES = 3

# MEMORY & CONTEXT CONSTANTS

# Short-term memory expiration (in seconds)
# Messages older than this are automatically pruned
STM_MAX_AGE = 3600  # 1 hour

# Long-term memory minimum similarity threshold
# Chunks with similarity < this are considered new/unique
LTM_MIN_SIMILARITY = 0.3

# RAG document chunking configuration
RAG_CHUNK_SIZE = 256  # tokens
RAG_CHUNK_OVERLAP = 50  # tokens

# Embedder cache settings
EMBEDDER_CACHE_ENABLED = True
EMBEDDER_MAX_CACHE_SIZE = 10000  # entries

# PROCESSING & FORMATTING CONSTANTS

# Markdown to ASCII table conversion
TABLE_MAX_WIDTH = 100  # characters
TABLE_MIN_COLUMN_WIDTH = 3  # characters

# Message processing
MAX_CONTENT_SIZE = 500000  # characters
MIN_CONTENT_SIZE = 1  # character

# URL processing
URL_REGEX_PATTERN = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+\/?(?:[^\s]*[^\s.,])?'

# MONITORING & RESOURCE CONSTANTS

# Resource monitoring intervals
RESOURCE_MONITOR_INTERVAL = 5.0  # seconds
RESOURCE_EXPORT_INTERVAL = 30.0  # seconds
RESOURCE_COLLECTION_INTERVAL = 1.0  # seconds

# Resource monitoring thresholds for alerts
ALERT_CPU_PERCENT_THRESHOLD = 50.0  # %
ALERT_MEMORY_MB_THRESHOLD = 500.0  # MB

# Resource history retention
RESOURCE_MAX_AGE_HOURS = 4
RESOURCE_MAX_SAMPLES = 1000

# API & INTEGRATION CONSTANTS

# Default API timeouts
DEFAULT_API_TIMEOUT = 30  # seconds
LONG_OPERATION_TIMEOUT = 300  # seconds (5 minutes)

# Rate limiting
DEFAULT_RATE_LIMIT = 10  # requests
RATE_LIMIT_WINDOW = 60  # seconds

# DOCUMENT PROCESSING CONSTANTS

# Supported document types for conversion
SUPPORTED_DOC_TYPES = [
    "pdf",
    "docx",
    "doc",
    "txt",
    "md",
    "html",
    "htm"
]

# File download timeout
FILE_DOWNLOAD_TIMEOUT = 30  # seconds

# Maximum file size for processing
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# LOGGING & DEBUGGING CONSTANTS

# Log levels
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"

# Default log level
DEFAULT_LOG_LEVEL = "INFO"

# FEATURE FLAGS & OPTIONS

# Enable/disable features
FEATURES = {
    "memory": True,
    "history": True,
    "preprompt": True,
    "internet": False,
    "audio": False,
    "image": True,
    "tools": False,
    "raw_mode": False
}

# ENCODING & FORMAT CONSTANTS

# Default character encoding
DEFAULT_ENCODING = "utf-8"

# Supported encodings for document processing
SUPPORTED_ENCODINGS = [
    "utf-8",
    "utf-16",
    "ascii",
    "latin-1"
]

# VALIDATION CONSTANTS

# Username/ID validation
MIN_USERNAME_LENGTH = 1
MAX_USERNAME_LENGTH = 32

# Query validation
MIN_QUERY_LENGTH = 1
MAX_QUERY_LENGTH = 4000

# Response validation
MIN_RESPONSE_LENGTH = 1
MAX_RESPONSE_LENGTH = 10000


# HELPER FUNCTIONS FOR ACCESSING CONSTANTS

def get_voice_by_priority(index: int = 0) -> str:
    """Get a voice by priority index.
    
    Args:
        index: Priority index (0-12 in order of preference).
        
    Returns:
        Voice name or DEFAULT_VOICE if index out of range.
    """
    if 0 <= index < len(AVAILABLE_VOICES):
        return AVAILABLE_VOICES[index]
    return DEFAULT_VOICE


def get_fallback_model(is_edit: bool = False) -> list:
    """Get appropriate fallback chain for the operation.
    
    Args:
        is_edit: True for image editing, False for generation.
        
    Returns:
        List of fallback model names.
    """
    return EDIT_FALLBACK_CHAIN if is_edit else DEFAULT_FALLBACK_CHAIN


def get_selector_endpoint(priority: int = 0) -> dict:
    """Get selector endpoint by priority.
    
    Args:
        priority: Priority order (0=first, 1=second, etc.).
        
    Returns:
        Endpoint configuration dict or empty dict if unavailable.
    """
    endpoints = [
        SELECTOR_ENDPOINTS.get("openrouter", {}),
        SELECTOR_ENDPOINTS.get("hackclub", {}),
        SELECTOR_ENDPOINTS.get("io_intelligence", {})
    ]
    if 0 <= priority < len(endpoints):
        return endpoints[priority]
    return {}


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled.
    
    Args:
        feature_name: Feature name to check.
        
    Returns:
        True if feature is enabled, False otherwise.
    """
    return FEATURES.get(feature_name, False)
