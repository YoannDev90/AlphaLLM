"""Module de mémoire STM/LTM - Gestion de la mémoire conversationnelle avec ChromaDB"""

import logging
from typing import Optional
import os

# Disable ChromaDB telemetry BEFORE importing anything from ChromaDB
os.environ["CHROMA_TELEMETRY_DISABLED"] = "true"

from utils.memory.embedder import TextEmbedder
from utils.memory.manager import MemoryManager
from utils.memory.config import STM_MAX_AGE, LTM_MIN_SIMILARITY

__all__ = [
    "TextEmbedder",
    "MemoryManager",
    "STM_MAX_AGE",
    "LTM_MIN_SIMILARITY",
    "initialize",
    "get_memory_manager",
]

logger = logging.getLogger("AlphaLLM")

# Variables globales pour le gestionnaire de mémoire
_memory_manager: Optional[MemoryManager] = None
_text_embedder: Optional[TextEmbedder] = None


async def initialize() -> None:
    """Initialise le gestionnaire de mémoires
    
    Crée et initialise une instance de MemoryManager avec ChromaDB Cloud
    """
    global _memory_manager, _text_embedder
    logger.debug("Initialisation du système de mémoire (STM + LTM)")
    _text_embedder = TextEmbedder()
    _memory_manager = MemoryManager(embedder=_text_embedder)
    await _memory_manager.initialize()


def get_memory_manager() -> MemoryManager:
    """Retourne l'instance du gestionnaire de mémoires
    
    Returns:
        L'instance MemoryManager
        
    Raises:
        RuntimeError: Si le gestionnaire n'a pas été initialisé
    """
    global _memory_manager
    if _memory_manager is None:
        raise RuntimeError("MemoryManager non initialisé. Appelez initialize() d'abord.")
    return _memory_manager

