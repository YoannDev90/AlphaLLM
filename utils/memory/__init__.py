"""Memory helpers aligned with the refactor plan."""

from __future__ import annotations

import logging
from typing import Optional

from utils.memory.chroma_manager import ChromaMemoryManager
from utils.memory.embedder import TextEmbedder
from utils.memory.manager import MemoryManager
from utils.memory.rag_handler import DocumentChunker, RAGDocumentHandler

_logger = logging.getLogger(__name__)
_memory_manager: Optional[MemoryManager] = None


async def initialize_memory_manager(embedder: Optional[TextEmbedder] = None) -> MemoryManager:
    """Initialize the shared memory manager and its downstream services."""

    global _memory_manager
    if _memory_manager is None:
        _logger.debug("Creating shared MemoryManager instance")
        _memory_manager = MemoryManager(embedder=embedder)
        await _memory_manager.initialize()
        _logger.info("Shared MemoryManager ready")
    return _memory_manager


async def get_memory_manager(embedder: Optional[TextEmbedder] = None) -> MemoryManager:
    """Return the shared MemoryManager, initializing it if needed."""

    if _memory_manager is None:
        await initialize_memory_manager(embedder=embedder)
    assert _memory_manager is not None
    return _memory_manager


__all__ = [
    "TextEmbedder",
    "ChromaMemoryManager",
    "MemoryManager",
    "DocumentChunker",
    "RAGDocumentHandler",
    "initialize_memory_manager",
    "get_memory_manager",
]
