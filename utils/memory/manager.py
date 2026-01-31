"""Coordinator for conversational memory features."""

import logging
from typing import Dict, List, Optional, Tuple

from utils.memory.faiss_manager import FaissMemoryManager
from utils.memory.micro_llm import MicroLLMHandler
from utils.memory.rag_handler import RAGDocumentHandler


class MemoryManager:
    """Provides STM/LTM access and RAG orchestration with Faiss."""

    def __init__(
        self,
        faiss_manager: Optional[FaissMemoryManager] = None,
        rag_handler: Optional[RAGDocumentHandler] = None,
        micro_llm: Optional[MicroLLMHandler] = None,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._faiss_manager = faiss_manager or FaissMemoryManager()
        self._rag_handler = rag_handler or RAGDocumentHandler(
            embedder=self._faiss_manager.embedder, faiss_manager=self._faiss_manager
        )
        self._micro_llm = micro_llm or MicroLLMHandler()
        self._logger.debug("MemoryManager configured with Faiss and micro LLM")

    @property
    def faiss_manager(self) -> FaissMemoryManager:
        return self._faiss_manager

    @property
    def rag_handler(self) -> RAGDocumentHandler:
        return self._rag_handler

    @property
    def micro_llm(self) -> MicroLLMHandler:
        return self._micro_llm

    async def initialize(self) -> None:
        await self._rag_handler.initialize()
        self._logger.debug("MemoryManager initialized")

    # Faiss methods
    async def add_memory(self, id: str, text: str, metadata: Optional[Dict] = None):
        await self._faiss_manager.add_memory(id, text, metadata)

    async def search_memories(
        self, query: str, top_k: int = 20, synthesize: bool = False
    ) -> str:
        """Search memories and optionally synthesize with micro LLM."""
        memories = await self._faiss_manager.search_memories(query, top_k)

        if synthesize and memories:
            return await self._micro_llm.synthesize_memories(query, memories)
        else:
            return "\n".join(memories)

    async def clear_memories(self):
        self._faiss_manager.clear_memories()

    async def store_document(
        self,
        user_id: int,
        server_id: int,
        document_text: str,
        document_id: str,
        metadata: Optional[Dict] = None,
    ) -> Tuple[str, int]:
        return await self._rag_handler.add_document(
            user_id, server_id, document_text, document_id, metadata
        )

    async def search_documents(
        self, user_id: int, server_id: int, query: str, limit: int = 10
    ) -> Dict[str, List]:
        return await self._rag_handler.search_documents(
            user_id, server_id, query, limit
        )

    async def get_hybrid_memories(
        self, user_id: int, conv_id: str, input: str, recent_limit: int = 4, similar_limit: int = 5
    ) -> Dict[str, List]:
        """Get hybrid memories: STM from database (not implemented), LTM from Faiss search."""
        # For now, return empty lists since STM is not implemented in this manager
        # LTM could be searched in Faiss, but for conversation, it's not stored there
        # TODO: Implement proper STM from database and LTM from vector search
        return {"stm": [], "ltm": []}
