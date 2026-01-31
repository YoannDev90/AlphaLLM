"""Coordinator for conversational memory features."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tinydb import Query, TinyDB

from config import MAX_STM_MESSAGES
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
        self._db_path = Path("data/conversation_memory.json")
        self._db_path.parent.mkdir(exist_ok=True)
        self._db = TinyDB(self._db_path)
        self._query = Query()
        self._logger.debug("MemoryManager configured with Faiss, TinyDB and micro LLM")

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
        await self._faiss_manager.initialize()
        await self._rag_handler.initialize()
        self._logger.debug("MemoryManager initialized")

    async def store_conversation_message(
        self, user_id: int, conv_id: str, content: str, role: str
    ):
        """Store a conversation message in TinyDB."""
        import time

        self._db.insert(
            {
                "user_id": user_id,
                "conv_id": conv_id,
                "content": content,
                "role": role,
                "timestamp": time.time(),
            }
        )
        # Keep only last MAX_STM_MESSAGES messages per conversation
        messages = self._db.search(
            (self._query.user_id == user_id) & (self._query.conv_id == conv_id)
        )
        if len(messages) > MAX_STM_MESSAGES:
            # Sort by timestamp and remove oldest
            messages.sort(key=lambda x: x["timestamp"])
            to_remove = messages[:-MAX_STM_MESSAGES]
            for msg in to_remove:
                self._db.remove(doc_ids=[msg.doc_id])
        self._logger.debug(f"Stored message for user {user_id}, conv {conv_id}")

    async def get_conversation_messages(
        self, user_id: int, conv_id: str, limit: int = 10
    ) -> List[Dict]:
        """Get recent conversation messages from TinyDB."""
        messages = self._db.search(
            (self._query.user_id == user_id) & (self._query.conv_id == conv_id)
        )
        messages.sort(key=lambda x: x["timestamp"])
        return messages[-limit:] if messages else []

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

    async def delete_stm_messages(self, doc_ids: List[int]):
        """Delete STM messages by doc_ids."""
        for doc_id in doc_ids:
            self._db.remove(doc_ids=[doc_id])
        self._logger.debug(f"Deleted {len(doc_ids)} STM messages")
