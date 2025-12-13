"""Coordinator for conversational memory features."""
import logging
from typing import Dict, List, Optional, Tuple

from utils.memory.chroma_manager import ChromaMemoryManager
from utils.memory.embedder import TextEmbedder
from utils.memory.rag_handler import RAGDocumentHandler


class MemoryManager:
    """Provides STM/LTM access and RAG orchestration."""

    def __init__(
        self,
        embedder: Optional[TextEmbedder] = None,
        chroma_manager: Optional[ChromaMemoryManager] = None,
        rag_handler: Optional[RAGDocumentHandler] = None,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._embedder = embedder or TextEmbedder()
        self._chroma_manager = chroma_manager or ChromaMemoryManager(embedder=self._embedder)
        self._rag_handler = rag_handler or RAGDocumentHandler(embedder=self._embedder)
        self._logger.debug("MemoryManager configured")

    @property
    def chroma_manager(self) -> ChromaMemoryManager:
        return self._chroma_manager

    @property
    def rag_handler(self) -> RAGDocumentHandler:
        return self._rag_handler

    @property
    def embedder(self) -> TextEmbedder:
        return self._embedder

    async def initialize(self) -> None:
        await self._chroma_manager.initialize()
        await self._rag_handler.initialize()
        self._logger.debug("MemoryManager initialized")

    async def add_conversation_message(self, user_id: int, server_id: int, text: str, role: str = "user") -> str:
        return await self._chroma_manager.add_conversation_message(user_id, server_id, text, role)

    async def add_long_term_memory(self, user_id: int, server_id: int, title: str, content: str, category: str = "general") -> str:
        return await self._chroma_manager.add_long_term_memory(user_id, server_id, title, content, category)

    async def update_long_term_memory(self, user_id: int, server_id: int, title: str, content: str, category: str = "general") -> str:
        return await self._chroma_manager.update_long_term_memory(user_id, server_id, title, content, category)

    async def add_document(self, user_id: int, server_id: int, text_clair: str, text_embed: str) -> bool:
        return await self._chroma_manager.add_document(user_id, server_id, text_clair, text_embed)

    async def add_memory(self, user_id: int, server_id: int, text_to_embed: str) -> str:
        return await self._chroma_manager.add_memory(user_id, server_id, text_to_embed)

    async def get_memories(self, user_id: int, server_id: int, limit_stm: int = 5, limit_ltm: int = 3) -> Dict[str, List[Dict]]:
        return await self._chroma_manager.get_memories(user_id, server_id, limit_stm, limit_ltm)

    async def get_long_term_memories(self, user_id: int, server_id: int, limit: int = 100) -> List[Dict]:
        return await self._chroma_manager.get_long_term_memories(user_id, server_id, limit)

    async def search_memories(self, user_id: int, server_id: int, query: str, limit: int = 5, memory_type: str = "both") -> Dict[str, List[Dict]]:
        return await self._chroma_manager.search_memories(user_id, server_id, query, limit, memory_type)

    async def get_hybrid_memories(self, user_id: int, server_id: int, current_query: str, recent_limit: int = 3, similar_limit: int = 5) -> Dict[str, List[Dict]]:
        return await self._chroma_manager.get_hybrid_memories(user_id, server_id, current_query, recent_limit, similar_limit)

    async def clear_history(self, user_id: int, server_id: Optional[int] = None, memory_type: str = "stm") -> int:
        return await self._chroma_manager.clear_history(user_id, server_id, memory_type)

    async def delete_stm_memories(self, ids: List[str]) -> None:
        await self._chroma_manager.delete_stm_memories(ids)

    async def store_document(self, user_id: int, server_id: int, document_text: str, document_id: str, metadata: Optional[Dict] = None) -> Tuple[str, int]:
        return await self._rag_handler.add_document(user_id, server_id, document_text, document_id, metadata)

    async def search_documents(self, user_id: int, server_id: int, query: str, limit: int = 10) -> Dict[str, List]:
        return await self._rag_handler.search_documents(user_id, server_id, query, limit)
