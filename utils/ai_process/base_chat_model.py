import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=True)
class ChatParameters:
    """Paramètres typés pour les conversations"""

    messages: List[Dict[str, Any]]
    model: str
    history: bool = True
    internet_access: bool = False
    files: Optional[List[str]] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    raw: bool = True


@dataclass(frozen=True)
class ChatResult:
    """Résultat d'une conversation"""

    response: str
    usage: int
    model: str
    elapsed_time: str


@dataclass(frozen=True)
class StreamChunk:
    """Chunk de streaming"""

    chunk: str
    done: bool
    response: Optional[str] = None
    usage: Optional[int] = None
    model: Optional[str] = None
    elapsed_time: Optional[str] = None


class BaseChatModel(ABC):
    """Classe de base abstraite pour tous les modèles de chat"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._configs_cache: Optional[List[Dict[str, Any]]] = None

    @abstractmethod
    async def chat(
        self, parameters: ChatParameters
    ) -> Union[ChatResult, AsyncGenerator[StreamChunk, None]]:
        """Méthode principale pour converser avec le modèle"""
        pass

    def _load_configs(self) -> List[Dict[str, Any]]:
        """Charge les configurations depuis le fichier JSON (avec cache)"""
        if self._configs_cache is not None:
            return self._configs_cache

        try:
            import json

            with open(self.config_path, "r") as f:
                raw_configs = json.load(f)

            for config in raw_configs:
                litellm_params = config.get("litellm_params", {})
                if "api_base" in litellm_params:
                    api_base = litellm_params["api_base"]
                    api_base = re.sub(
                        r"<(\w+)>", lambda m: os.environ.get(m.group(1), ""), api_base
                    )
                    litellm_params["api_base"] = api_base

            self._configs_cache = raw_configs
            return raw_configs
        except Exception as e:
            logger.error(
                f"Erreur lors du chargement des configs {self.config_path}: {e}"
            )
            raise

    def _format_elapsed_time(self, start_time: datetime) -> str:
        """Formate le temps écoulé"""
        elapsed_time = datetime.now() - start_time
        minutes = elapsed_time.seconds // 60
        seconds = elapsed_time.seconds % 60
        milliseconds = elapsed_time.microseconds // 1000

        if minutes > 0:
            return f"{minutes} minutes, {seconds}.{milliseconds:03d} seconds"
        else:
            return f"{seconds}.{milliseconds:03d} seconds"
