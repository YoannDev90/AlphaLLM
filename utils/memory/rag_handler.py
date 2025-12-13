"""Standalone document chunking and RAG helpers."""
import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

from config import (CHROMA_API_KEY, CHROMA_DB_NAME, CHROMA_LTM_COLLECTION,
                    CHROMA_RAG_COLLECTION, CHROMA_STM_COLLECTION,
                    CHROMA_TENANT_ID, LOGGER_NAME)
from utils.memory.embedder import TextEmbedder

logger = logging.getLogger(LOGGER_NAME)


class DocumentChunker:
    """Splits long text into manageable chunks for embedding storage."""

    def __init__(self, chunk_size: int = 256, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.avg_chars_per_token = 4.5
        logger.debug("DocumentChunker configured chunk_size=%s overlap=%s", chunk_size, overlap)

    def estimate_tokens(self, text: str) -> int:
        return int(len(text) / self.avg_chars_per_token)

    def _split_sentences(self, text: str) -> List[str]:
        return [sentence.strip() for sentence in text.replace("\n\n", ".\n").split('.') if sentence.strip()]

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
                chunks.append(' '.join(current))
                overlap_count = max(1, len(current) // 2)
                current = current[-overlap_count:]
                current_tokens = sum(self.estimate_tokens(s) for s in current)

            current.append(sentence)
            current_tokens += sentence_tokens

        if current:
            chunks.append(' '.join(current))

        logger.debug("Chunked text into %s segments", len(chunks))
        return chunks

    def chunk_by_paragraph(self, text: str) -> List[str]:
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks: List[str] = []
        current: List[str] = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self.estimate_tokens(para)
            if current and current_tokens + para_tokens > self.chunk_size:
                chunks.append('\n\n'.join(current))
                current = []
                current_tokens = 0

            current.append(para)
            current_tokens += para_tokens

        if current:
            chunks.append('\n\n'.join(current))

        logger.debug("Paragraph chunked text into %s segments", len(chunks))
        return chunks


class RAGDocumentHandler:
    """Handles document ingestion and retrieval backed by ChromaDB."""

    def __init__(self, embedder: Optional[TextEmbedder] = None, chunker: Optional[DocumentChunker] = None) -> None:
        self._logger = logging.getLogger(__name__)
        self._embedder = embedder or TextEmbedder()
        self._chunker = chunker or DocumentChunker()
        self._client: Optional[chromadb.CloudClient] = None
        self._collection: Optional[Collection] = None
        self._logger.debug("RAGDocumentHandler constructed")

    @property
    def embedder(self) -> TextEmbedder:
        return self._embedder

    @property
    def chunker(self) -> DocumentChunker:
        return self._chunker

    async def initialize(self) -> None:
        if not CHROMA_TENANT_ID or not CHROMA_API_KEY:
            raise RuntimeError("Missing ChromaDB credentials for RAGDocumentHandler")

        if self._collection:
            return

        self._logger.debug("Initializing ChromaDB CloudClient")
        self._client = chromadb.CloudClient(
            api_key=CHROMA_API_KEY,
            tenant=CHROMA_TENANT_ID,
            database=CHROMA_DB_NAME,
            settings=Settings()
        )
        self._collection = self._client.get_or_create_collection(CHROMA_RAG_COLLECTION)
        self._logger.info("ChromaDB collection %s initialized", CHROMA_RAG_COLLECTION)

    def _ensure_collection(self) -> Collection:
        if not self._collection:
            raise RuntimeError("RAGDocumentHandler not initialized")
        return self._collection

    def _generate_chunk_id(self, user_id: int, server_id: int, document_id: str, chunk_index: int) -> str:
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
        collection = self._ensure_collection()
        chunks = self._chunker.chunk_by_token_count(document_text)
        if not chunks:
            self._logger.warning("Document %s produced no chunks", document_id)
            return document_id, 0

        chunk_ids: List[str] = []
        embeddings: List[List[float]] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        base_metadata = {
            "user_id": user_id,
            "server_id": server_id,
            "document_id": document_id,
            "created_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }

        # generate embeddings in batch to reduce latency
        generated_embeddings = self._embedder.embed_batch(chunks)
        for index, chunk in enumerate(chunks):
            chunk_id = self._generate_chunk_id(user_id, server_id, document_id, index)
            chunk_metadata = {
                **base_metadata,
                "chunk_index": index,
                "chunk_count": len(chunks),
                "chunk_size_tokens": self._chunker.estimate_tokens(chunk),
            }

            chunk_ids.append(chunk_id)
            embeddings.append(generated_embeddings[index])
            documents.append(chunk)
            metadatas.append(chunk_metadata)

        collection.add(ids=chunk_ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        self._logger.info("Stored document %s with %s chunks", document_id, len(chunks))
        return document_id, len(chunks)

    async def retrieve_relevant_chunks(
        self,
        user_id: int,
        server_id: int,
        query: str,
        k: int = 5,
        min_relevance: float = 0.3,
    ) -> List[Dict[str, Any]]:
        collection = self._ensure_collection()
        query_embedding = self._embedder.embed(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"server_id": {"$eq": server_id}},
                ]
            },
            n_results=k,
            include=["metadatas", "documents", "distances"],
        )

        retrieved: List[Dict[str, Any]] = []
        ids = results.get("ids", [])
        distances = results.get("distances", [])
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])

        if ids and ids[0]:
            ids_list = ids[0] if isinstance(ids[0], list) else ids
            for idx, chunk_id in enumerate(ids_list):
                distance = distances[0][idx]
                similarity = 1 - (distance / 2)
                if similarity < min_relevance:
                    continue
                retrieved.append(
                    {
                        "id": chunk_id,
                        "content": documents[0][idx],
                        "metadata": metadatas[0][idx],
                        "relevance_score": similarity,
                        "distance": distance,
                    }
                )

        self._logger.debug("Retrieved %s relevant chunks", len(retrieved))
        return retrieved

    async def get_document_summary(self, user_id: int, server_id: int, document_id: str) -> Optional[Dict[str, Any]]:
        collection = self._ensure_collection()
        results = collection.get(
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"server_id": {"$eq": server_id}},
                    {"document_id": {"$eq": document_id}},
                ]
            },
            include=["metadatas", "documents"],
        )

        ids = list(results.get("ids") or [])
        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []

        if not ids:
            self._logger.warning("Document %s not found", document_id)
            return None

        chunks = [
            {
                "index": metadatas[i].get("chunk_index", i),
                "content": documents[i],
                "size_tokens": metadatas[i].get("chunk_size_tokens", 0),
            }
            for i in range(len(ids))
        ]

        summary = {
            "document_id": document_id,
            "created_at": metadatas[0].get("created_at"),
            "chunk_count": len(chunks),
            "total_tokens": sum(chunk["size_tokens"] for chunk in chunks),
            "chunks": chunks,
        }
        self._logger.info("Document %s summary assembled", document_id)
        return summary

    async def delete_document(self, user_id: int, server_id: int, document_id: str) -> int:
        collection = self._ensure_collection()
        results = collection.get(
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"server_id": {"$eq": server_id}},
                    {"document_id": {"$eq": document_id}},
                ]
            }
        )

        ids = list(results.get("ids") or [])
        if not ids:
            return 0

        collection.delete(ids=ids)
        self._logger.info("Deleted document %s (%s chunks)", document_id, len(ids))
        return len(ids)

    async def search_documents(self, user_id: int, server_id: int, query: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        chunks = await self.retrieve_relevant_chunks(user_id, server_id, query, k=limit)
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for chunk in chunks:
            doc_id = chunk["metadata"].get("document_id", "unknown")
            grouped.setdefault(doc_id, []).append(chunk)
        self._logger.info("Search matched %s documents", len(grouped))
        return grouped
