"""Standalone document chunking and RAG helpers."""

import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from utils.memory.embedder import TextEmbedder
from utils.memory.faiss_manager import FaissMemoryManager

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Splits long text into manageable chunks for embedding storage."""

    def __init__(self, chunk_size: int = 256, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.avg_chars_per_token = 4.5
        logger.debug(
            f"DocumentChunker configured chunk_size={chunk_size} overlap={overlap}"
        )

    def estimate_tokens(self, text: str) -> int:
        return int(len(text) / self.avg_chars_per_token)

    def _split_sentences(self, text: str) -> List[str]:
        return [
            sentence.strip()
            for sentence in text.replace("\n\n", ".\n").split(".")
            if sentence.strip()
        ]

    def chunk_by_token_count(self, text: str) -> List[str]:
        sentences = self._split_sentences(text)
        chunks: List[str] = []
        current: List[str] = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.estimate_tokens(sentence)
            if sentence_tokens == 0:
                continue

            if current_tokens + sentence_tokens > self.chunk_size and current:
                chunks.append(" ".join(current))
                overlap_count = max(1, len(current) // 2)
                current = current[-overlap_count:]
                current_tokens = sum(self.estimate_tokens(s) for s in current)

            current.append(sentence)
            current_tokens += sentence_tokens

        if current:
            chunks.append(" ".join(current))

        logger.debug(f"Chunked text into {len(chunks)} segments")
        return chunks

    def chunk_by_paragraph(self, text: str) -> List[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        current: List[str] = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self.estimate_tokens(para)
            if current and current_tokens + para_tokens > self.chunk_size:
                chunks.append("\n\n".join(current))
                current = []
                current_tokens = 0

            current.append(para)
            current_tokens += para_tokens

        if current:
            chunks.append("\n\n".join(current))

        logger.debug(f"Paragraph chunked text into {len(chunks)} segments")
        return chunks


class RAGDocumentHandler:
    """Handles document ingestion and retrieval backed by Faiss."""

    def __init__(
        self,
        embedder: Optional[TextEmbedder] = None,
        chunker: Optional[DocumentChunker] = None,
        faiss_manager: Optional[FaissMemoryManager] = None,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._embedder = embedder or TextEmbedder()
        self._chunker = chunker or DocumentChunker()
        self._faiss_manager = faiss_manager or FaissMemoryManager(
            embedder=self._embedder
        )
        self._logger.debug("RAGDocumentHandler constructed")

    @property
    def embedder(self) -> TextEmbedder:
        return self._embedder

    @property
    def chunker(self) -> DocumentChunker:
        return self._chunker

    async def initialize(self) -> None:
        # Faiss doesn't need special initialization
        self._logger.info("Faiss-based RAGDocumentHandler initialized")

    def _generate_chunk_id(
        self, user_id: int, server_id: int, document_id: str, chunk_index: int
    ) -> str:
        base = f"rag:{user_id}:{server_id}:{document_id}:{chunk_index}:{time.time_ns()}"
        return hashlib.sha256(base.encode()).hexdigest()

    async def add_document(
        self,
        user_id: int,
        server_id: int,
        document_text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, int]:
        chunks = self._chunker.chunk_by_token_count(document_text)
        if not chunks:
            self._logger.warning(f"Document {document_id} produced no chunks")
            return document_id, 0

        base_metadata = {
            "user_id": user_id,
            "server_id": server_id,
            "document_id": document_id,
            "created_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }

        for index, chunk in enumerate(chunks):
            chunk_id = self._generate_chunk_id(user_id, server_id, document_id, index)
            chunk_metadata = {
                **base_metadata,
                "chunk_index": index,
                "chunk_count": len(chunks),
                "chunk_size_tokens": self._chunker.estimate_tokens(chunk),
            }
            await self._faiss_manager.add_memory(chunk_id, chunk, chunk_metadata)

        self._logger.info(f"Stored document {document_id} with {len(chunks)} chunks")
        return document_id, len(chunks)

    async def retrieve_relevant_chunks(
        self,
        user_id: int,
        server_id: int,
        query: str,
        k: int = 5,
        min_relevance: float = 0.3,
    ) -> List[Dict[str, Any]]:
        # For Faiss, we can't filter by user/server easily, so we'll search all and filter
        results = await self._faiss_manager.search_with_metadata(
            query, top_k=k * 2
        )  # Get more to filter

        retrieved: List[Dict[str, Any]] = []
        for item in results:
            meta = item["metadata"]
            if meta.get("user_id") == user_id and meta.get("server_id") == server_id:
                distance = item["distance"]
                similarity = 1 - (distance / 2)  # Cosine distance to similarity
                if similarity >= min_relevance:
                    retrieved.append(
                        {
                            "id": meta.get("id", "unknown"),
                            "content": item["text"],
                            "metadata": meta,
                            "relevance_score": similarity,
                            "distance": distance,
                        }
                    )
                if len(retrieved) >= k:
                    break

        self._logger.debug(f"Retrieved {len(retrieved)} relevant chunks")
        return retrieved

    async def get_document_summary(
        self, user_id: int, server_id: int, document_id: str
    ) -> Optional[Dict[str, Any]]:
        chunks = self._faiss_manager.get_by_metadata_filter(
            lambda m: m.get("user_id") == user_id
            and m.get("server_id") == server_id
            and m.get("document_id") == document_id
        )

        if not chunks:
            self._logger.warning(f"Document {document_id} not found")
            return None

        chunk_summaries = [
            {
                "index": item["metadata"].get("chunk_index", i),
                "content": item["text"],
                "size_tokens": item["metadata"].get("chunk_size_tokens", 0),
            }
            for i, item in enumerate(chunks)
        ]

        summary = {
            "document_id": document_id,
            "created_at": chunks[0]["metadata"].get("created_at"),
            "chunk_count": len(chunks),
            "total_tokens": sum(c["size_tokens"] for c in chunk_summaries),
            "chunks": chunk_summaries,
        }
        self._logger.info(f"Document {document_id} summary assembled")
        return summary

    async def delete_document(
        self, user_id: int, server_id: int, document_id: str
    ) -> int:
        deleted = self._faiss_manager.delete_by_metadata_filter(
            lambda m: m.get("user_id") == user_id
            and m.get("server_id") == server_id
            and m.get("document_id") == document_id
        )
        self._logger.info(f"Deleted document {document_id} ({deleted} chunks)")
        return deleted

    async def search_documents(
        self, user_id: int, server_id: int, query: str, limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        chunks = await self.retrieve_relevant_chunks(user_id, server_id, query, k=limit)
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for chunk in chunks:
            doc_id = chunk["metadata"].get("document_id", "unknown")
            grouped.setdefault(doc_id, []).append(chunk)
        self._logger.info(f"Search matched {len(grouped)} documents")
        return grouped
