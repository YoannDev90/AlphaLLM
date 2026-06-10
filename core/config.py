"""Configuration loading and prompt helpers for AlphaLLM."""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    import tomllib as _toml
except Exception:
    try:
        import toml as _toml  # type: ignore
    except Exception:
        _toml = None

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    print(
        "Warning: python-dotenv not installed, environment variables from .env will not be loaded."
    )

# base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "config.toml")


def _load_toml(path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load and parse a TOML configuration file.

    Parameters
    ----------
    path : str
        Path to the TOML file. Default is DEFAULT_CONFIG_PATH.

    Returns
    -------
    Dict[str, Any]
        Parsed TOML content or an empty dict.
    """
    if _toml is None:
        return {}
    if os.path.exists(path):
        with open(
            path,
            "rb"
            if hasattr(_toml, "loads")
            and _toml is not None
            and hasattr(_toml, "__name__")
            and _toml.__name__ == "tomllib"
            else "r",
            encoding=None
            if hasattr(_toml, "loads")
            and _toml is not None
            and hasattr(_toml, "__name__")
            and _toml.__name__ == "tomllib"
            else "utf-8",
        ) as f:
            # tomllib expects bytes I/O in py3.11, toml package expects text
            if getattr(_toml, "__name__", "") == "tomllib":
                return _toml.load(f)
            else:
                return _toml.load(f)
    return {}


def read_from_toml_config(
    param: str, config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Read a nested config table from TOML data.

    Parameters
    ----------
    param : str
        Section name to read.
    config : Optional[Dict[str, Any]]
        Preloaded config mapping. Default is None.

    Returns
    -------
    Dict[str, Any]
        Section contents or an empty dict.
    """
    cfg = config or _load_toml()
    return cfg.get(param, {}) if isinstance(cfg.get(param, {}), dict) else {}


@dataclass
class ConsoleLoggingConfig:
    """Console logging configuration.

    Attributes
    ----------
    enable : bool
        Whether console logging is enabled.
    level : str
        Console logging level.
    console_format : str
        Format string used for console logs.
    """

    enable: bool = True
    level: str = "INFO"
    console_format: str = "%(asctime)s - %(message)s"


@dataclass
class FileLoggingConfig:
    """File logging configuration.

    Attributes
    ----------
    enable_file_logging : bool
        Whether file logging is enabled.
    log_file : str
        Path to the log file.
    file_format : str
        Format string used for file logs.
    """

    enable_file_logging: bool = True
    log_file: str = "logs/alphallm.log"

    # file logs can keep more context; filename is more useful than logger name
    file_format: str = "%(asctime)s - %(filename)s - %(message)s"


@dataclass
class DiscordLoggingConfig:
    """Discord webhook logging configuration.

    Attributes
    ----------
    enable_discord_logging : bool
        Whether Discord logging is enabled.
    discord_webhook : Optional[str]
        Discord webhook URL.
    discord_format : str
        Format string used for Discord logs.
    """

    enable_discord_logging: bool = False
    discord_webhook: Optional[str] = None
    discord_format: str = "%(asctime)s - %(filename)s\n%(message)s"


@dataclass
class LoggingConfig:
    """Aggregated logging configuration.

    Attributes
    ----------
    console : ConsoleLoggingConfig
        Console logging settings.
    file : FileLoggingConfig
        File logging settings.
    discord : DiscordLoggingConfig
        Discord logging settings.
    level : str
        Console logging level.
    enable_file_logging : bool
        Whether file logging is enabled.
    log_file : str
        Log file path.
    enable_discord_logging : bool
        Whether Discord logging is enabled.
    discord_webhook : Optional[str]
        Discord webhook URL.
    console_format : str
        Console log format string.
    file_format : str
        File log format string.
    discord_format : str
        Discord log format string.
    """

    console: ConsoleLoggingConfig
    file: FileLoggingConfig
    discord: DiscordLoggingConfig

    @property
    def level(self) -> str:
        """Return the configured console log level.

        Returns
        -------
        str
            Console log level string.
        """
        return self.console.level

    @property
    def enable_file_logging(self) -> bool:
        """Return whether file logging is enabled.

        Returns
        -------
        bool
            True when file logging is enabled.
        """
        return self.file.enable_file_logging

    @property
    def log_file(self) -> str:
        """Return the file logging path.

        Returns
        -------
        str
            File logging path.
        """
        return self.file.log_file

    @property
    def enable_discord_logging(self) -> bool:
        """Return whether Discord logging is enabled.

        Returns
        -------
        bool
            True when Discord logging is enabled.
        """
        return self.discord.enable_discord_logging

    @property
    def discord_webhook(self) -> Optional[str]:
        """Return the configured Discord webhook URL.

        Returns
        -------
        Optional[str]
            Discord webhook URL or None.
        """
        return self.discord.discord_webhook

    @property
    def console_format(self) -> str:
        """Return the console log format string.

        Returns
        -------
        str
            Console log format string.
        """
        return self.console.console_format

    @property
    def file_format(self) -> str:
        """Return the file log format string.

        Returns
        -------
        str
            File log format string.
        """
        return self.file.file_format

    @property
    def discord_format(self) -> str:
        """Return the Discord log format string.

        Returns
        -------
        str
            Discord log format string.
        """
        return self.discord.discord_format


@dataclass
class Config:
    """Runtime config values resolved from environment and files.

    Attributes
    ----------
    DEV_IDS : List[int]
        List of Discord user IDs with developer privileges.
    LINKS : Dict[str, str]
        Configuration links such as support server and website.
    BOT_TOKEN : Optional[str]
        Discord bot token.
    WEBHOOK_POSTURL : Optional[str]
        Webhook path or id component.
    WEBHOOK_URL : Optional[str]
        Resolved webhook URL.
    BASE_DIR : str
        Repository base directory.
    SYSTEM_PROMPT_PATH : str
        Path to the system prompt file.
    PROVIDERS_PATH : str
        Path to the provider definitions.
    MODELS_PATH : str
        Path to the model definitions.
    MOODS_DIR : str
        Path to the mood prompt directory.
    CONFIG_PATH : str
        Path to the active config file.
    """

    # Load additional constants from configuration files
    @staticmethod
    def _load_perms_config() -> List[int]:
        """Load permissions configuration from perms.json."""
        perms_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "perms.json"
        )
        try:
            with open(perms_path, "r") as f:
                data = json.load(f)
                return data.get("dev_ids", [])
        except Exception:
            return []

    @staticmethod
    def _load_links_config() -> Dict[str, str]:
        """Load links configuration from links.json."""
        links_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "links.json"
        )
        try:
            with open(links_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"support_server": "", "website": ""}

    # Class properties to access configuration data
    @property
    def DEV_IDS(self) -> List[int]:
        """Get developer IDs from configuration file."""
        return self._load_perms_config()

    @property
    def LINKS(self) -> Dict[str, str]:
        """Get links configuration from configuration file."""
        return self._load_links_config()

    BOT_TOKEN: Optional[str] = None
    WEBHOOK_POSTURL: Optional[str] = None
    WEBHOOK_URL: Optional[str] = None

    # Path to system prompt and data
    BASE_DIR: str = BASE_DIR
    SYSTEM_PROMPT_PATH: str = os.path.join(BASE_DIR, "config", "system_prompt.txt")
    PROVIDERS_PATH: str = os.path.join(BASE_DIR, "config", "providers.json")
    MODELS_PATH: str = os.path.join(BASE_DIR, "config", "models.json")
    MOODS_DIR: str = os.path.join(BASE_DIR, "config", "moods")
    CONFIG_PATH: str = DEFAULT_CONFIG_PATH


def _first_table(items: Any) -> Dict[str, Any]:
    """Return the first dict from a TOML table-or-list value.

    Parameters
    ----------
    items : Any
        Value extracted from TOML.

    Returns
    -------
    Dict[str, Any]
        First mapping if available, otherwise an empty dict.
    """
    if isinstance(items, list) and items:
        return items[0] if isinstance(items[0], dict) else {}
    if isinstance(items, dict):
        return items
    return {}


def _normalize_webhook_url(url: Optional[str]) -> Optional[str]:
    """Normalize a Discord webhook URL or webhook id/path.

    Parameters
    ----------
    url : Optional[str]
        Input URL or webhook reference.

    Returns
    -------
    Optional[str]
        Normalized webhook URL or None.
    """
    if not url:
        return None
    # If the configured url contains a placeholder, substitute with env var WEBHOOK_URL
    if "<URL>" in url:
        env_val = os.getenv("WEBHOOK_URL")
        if not env_val:
            return None
        url = url.replace("<URL>", env_val)
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"https://discord.com/api/webhooks/{url.lstrip('/')}"


def load_config(config_path: Optional[str] = None) -> Tuple[Config, LoggingConfig]:
    """Load application and logging configuration.

    Parameters
    ----------
    config_path : Optional[str]
        Optional path to a TOML config file. Default is None.

    Returns
    -------
    Tuple[Config, LoggingConfig]
        Resolved app config and logging config.
    """
    toml_path = config_path or DEFAULT_CONFIG_PATH
    raw = _load_toml(toml_path)

    raw_logging = raw.get("logging", {}) if isinstance(raw, dict) else {}
    console_raw = _first_table(raw.get("console"))
    file_raw = _first_table(raw.get("file"))
    discord_raw = _first_table(raw.get("discord"))

    # Backward compatibility with previous flat schema if present under [logging]
    console_conf = ConsoleLoggingConfig(
        enable=console_raw.get("enable", raw_logging.get("enable", True)),
        level=console_raw.get("level", raw_logging.get("level", "INFO")),
        console_format=console_raw.get(
            "console_format",
            raw_logging.get("console_format", "%(asctime)s - %(message)s"),
        ),
    )
    file_conf = FileLoggingConfig(
        enable_file_logging=file_raw.get(
            "enable_file_logging", raw_logging.get("enable_file_logging", True)
        ),
        log_file=file_raw.get(
            "log_file", raw_logging.get("log_file", "logs/alphallm.log")
        ),
        file_format=file_raw.get(
            "file_format",
            raw_logging.get("file_format", "%(asctime)s - %(filename)s - %(message)s"),
        ),
    )
    discord_conf = DiscordLoggingConfig(
        enable_discord_logging=discord_raw.get(
            "enable_discord_logging",
            raw_logging.get("enable_discord_logging", False),
        ),
        discord_webhook=_normalize_webhook_url(
            discord_raw.get("discord_webhook")
            or raw_logging.get("discord_webhook")
            or None
        ),
        discord_format=discord_raw.get(
            "discord_format",
            raw_logging.get(
                "discord_format", "%(asctime)s - %(filename)s\n%(message)s"
            ),
        ),
    )

    logging_conf = LoggingConfig(
        console=console_conf,
        file=file_conf,
        discord=discord_conf,
    )

    cfg = Config()
    cfg.BOT_TOKEN = os.getenv("BOT_TOKEN")
    cfg.WEBHOOK_POSTURL = os.getenv("WEBHOOK_URL") or os.getenv("WEBHOOK_POSTURL")

    env_webhook_url = _normalize_webhook_url(os.getenv("WEBHOOK_URL"))

    # Determine final webhook URL: priority - env WEBHOOK_URL, logging.discord_webhook, combine webhook_base + posturl
    if env_webhook_url:
        cfg.WEBHOOK_URL = env_webhook_url
    elif logging_conf.discord_webhook:
        cfg.WEBHOOK_URL = logging_conf.discord_webhook
    else:
        # combine base + posturl if present
        root_webhook_base = raw.get("webhook_base") or raw.get("webhook", {}).get(
            "base"
        )
        if root_webhook_base:
            # If base contains placeholder, replace with env WEBHOOK_URL
            if "<URL>" in root_webhook_base:
                env_val = os.getenv("WEBHOOK_URL")
                if env_val:
                    substituted = root_webhook_base.replace("<URL>", env_val)
                    cfg.WEBHOOK_URL = _normalize_webhook_url(substituted)
            elif cfg.WEBHOOK_POSTURL:
                cfg.WEBHOOK_URL = (
                    root_webhook_base.rstrip("/")
                    + "/"
                    + cfg.WEBHOOK_POSTURL.lstrip("/")
                )

    cfg.CONFIG_PATH = toml_path
    return cfg, logging_conf


# load default config at import time
cfg, logging_cfg = load_config()


def read_system_prompt() -> Optional[str]:
    """Read the global system prompt from disk.

    Returns
    -------
    Optional[str]
        Prompt text or None when the file is missing.
    """
    if os.path.exists(cfg.SYSTEM_PROMPT_PATH):
        with open(cfg.SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def read_mood_prompt(mood: str | None) -> Optional[str]:
    """Read a mood-specific system prompt from `data/moods/<mood>.txt`.

    If `mood` is None or the file does not exist, fallback to `neutral.txt`.

    Parameters
    ----------
    mood : str | None
        Mood name to read.

    Returns
    -------
    Optional[str]
        Mood prompt text or None when unavailable.
    """
    moods_dir = os.path.join(BASE_DIR, "data", "moods")
    if mood:
        path = os.path.join(moods_dir, f"{mood}.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()

    # fallback to neutral
    fallback = os.path.join(moods_dir, "neutral.txt")
    if os.path.exists(fallback):
        with open(fallback, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None
