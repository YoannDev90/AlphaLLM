"""Chromadb-backed memory manager for STM/LTM operations."""

from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.api.models.Collection import Collection

from config import (CHROMA_API_KEY, CHROMA_DB_NAME, CHROMA_LTM_COLLECTION,
                    CHROMA_RAG_COLLECTION, CHROMA_STM_COLLECTION,
                    CHROMA_TENANT_ID, LOGGER_NAME, LTM_MIN_SIMILARITY,
                    STM_MAX_AGE)
from utils.memory.embedder import TextEmbedder


class ChromaMemoryManager:
    """API for storing and querying STM/LTM memories inside ChromaDB."""

    def __init__(self, embedder: Optional[TextEmbedder] = None, prefix: Optional[str] = None) -> None:
        self._logger = logging.getLogger(LOGGER_NAME)
        self._embedder = embedder or TextEmbedder()
        self._client: Optional[chromadb.CloudClient] = None
        self._stm_collection: Optional[Collection] = None
        self._ltm_collection: Optional[Collection] = None
        self._rag_collection: Optional[Collection] = None
        self._prefix = prefix or "default"
        self._stm_collection_name = CHROMA_STM_COLLECTION
        self._ltm_collection_name = CHROMA_LTM_COLLECTION
        self._rag_collection_name = CHROMA_RAG_COLLECTION
        self._logger.debug("ChromaMemoryManager configured (prefix=%s)")

    @property
    def embedder(self) -> TextEmbedder:
        return self._embedder

    async def initialize(self) -> None:
        """Establishes the Chromadb client and ensures STM/LTM collections exist."""
        if self._client:
            return

        if not CHROMA_TENANT_ID or not CHROMA_API_KEY:
            raise RuntimeError("Missing ChromaDB credentials for memory storage")

        try:
            self._logger.debug("Initializing Chromadb CloudClient")
            self._client = chromadb.CloudClient(
                tenant=CHROMA_TENANT_ID,
                database=CHROMA_DB_NAME,
                api_key=CHROMA_API_KEY,
            )
            self._stm_collection = self._client.get_or_create_collection(self._stm_collection_name)
            self._ltm_collection = self._client.get_or_create_collection(self._ltm_collection_name)
            self._logger.info(
                "ChromaDB collections initialized (stm=%s, ltm=%s)",
                self._stm_collection_name,
                self._ltm_collection_name,
            )
        except Exception as exc:  # pragma: no cover - rare failure path
            self._logger.error("Failed to initialize ChromaDB: %s", exc)
            raise

    def _require_collections(self) -> Tuple[Collection, Collection]:
        if not self._stm_collection or not self._ltm_collection:
            raise RuntimeError("ChromaMemoryManager is not initialized")
        return self._stm_collection, self._ltm_collection

    @staticmethod
    def _generate_id(user_id: int, server_id: int, prefix: str) -> str:
        base = f"{prefix}:{user_id}:{server_id}:{time.time_ns()}"
        return hashlib.sha256(base.encode()).hexdigest()

    @staticmethod
    def _content_hash(text: str) -> str:
        normalized = " ".join(text.strip().split()).lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    @staticmethod
    def _build_where_clause(user_id: int, server_id: Optional[int] = None) -> Dict[str, Any]:
        user_filter = {"user_id": {"$eq": user_id}}
        if server_id is None:
            return user_filter
        return {"$and": [user_filter, {"server_id": {"$eq": server_id}}]}

    async def _delete_old_stm_memories(self, user_id: int, server_id: int) -> None:
        stm_collection, _ = self._require_collections()
        try:
            results = stm_collection.get(
                where=self._build_where_clause(user_id, server_id),
                include=["metadatas"],
            )
            metadatas = results.get("metadatas") or []
            ids = list(results.get("ids") or [])
            if not metadatas:
                return

            now = datetime.utcnow().timestamp()
            expired_ids: List[str] = []

            for idx, metadata in enumerate(metadatas):
                created_at = metadata.get("created_at")
                if not created_at:
                    continue
                try:
                    age = now - datetime.fromisoformat(created_at).timestamp()
                except ValueError:
                    continue
                if age > STM_MAX_AGE:
                    expired_ids.append(ids[idx])
                    self._logger.debug("STM memory expired (id=%s, age=%.1fs)", ids[idx], age)

            if expired_ids:
                stm_collection.delete(ids=expired_ids)
                self._logger.info("Expired STM memories removed (%s entries)", len(expired_ids))
        except Exception as exc:
            self._logger.error("Failed to cleanup STM memories: %s", exc)

    async def add_conversation_message(self, user_id: int, server_id: int, text: str, role: str = "user") -> str:
        stm_collection, _ = self._require_collections()
        await self._delete_old_stm_memories(user_id, server_id)
        embedding = self._embedder.embed(text)
        entry_id = self._generate_id(user_id, server_id, prefix="stm")
        stm_collection.add(
            ids=[entry_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[
                {
                    "user_id": user_id,
                    "server_id": server_id,
                    "role": role,
                    "created_at": datetime.utcnow().isoformat(),
                }
            ],
        )
        self._logger.debug("STM message stored (id=%s, role=%s)", entry_id, role)
        return entry_id

    async def add_long_term_memory(self, user_id: int, server_id: int, title: str, content: str, category: str = "general", source: Optional[str] = None, confidence: Optional[float] = None) -> str:
        _, ltm_collection = self._require_collections()
        self._logger.debug("add_long_term_memory: user_id=%s, server_id=%s, title=%s, category=%s, source=%s, confidence=%s", user_id, server_id, title, category, source, confidence)
        content_hash = self._content_hash(content)
        self._logger.debug("content_hash computed: %s", content_hash)
        embedding = self._embedder.embed(content)
        self._logger.debug("embedding computed: len=%s", len(embedding))
        entry_id = self._generate_id(user_id, server_id, prefix="ltm")
        self._logger.debug("entry_id generated: %s", entry_id)
        metadata = {
            "user_id": user_id,
            "server_id": server_id,
            "title": title,
            "category": category,
            "content_hash": content_hash,
            "created_at": datetime.utcnow().isoformat(),
        }
        if source:
            metadata["source"] = source
        if confidence is not None:
            metadata["confidence"] = confidence
        self._logger.debug("metadata prepared: %s", metadata)
        ltm_collection.add(
            ids=[entry_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
        )
        self._logger.debug("added to ltm_collection")
        self._logger.info("LTM fact added: title='%s', content='%s...', category='%s', source='%s', confidence=%s", title, content[:50], category, source or 'manual', confidence)
        return entry_id

    async def update_long_term_memory(self, user_id: int, server_id: int, title: str, content: str, category: str = "general", source: Optional[str] = None, confidence: Optional[float] = None) -> str:
        _, ltm_collection = self._require_collections()
        self._logger.debug("update_long_term_memory: user_id=%s, server_id=%s, title=%s, category=%s, source=%s, confidence=%s", user_id, server_id, title, category, source, confidence)
        where = self._build_where_clause(user_id, server_id)
        if isinstance(where, dict) and "$and" in where:
            where = {"$and": where["$and"] + [{"title": {"$eq": title}}]}
        else:
            where = {"$and": [where, {"title": {"$eq": title}}]}
        self._logger.debug("where clause: %s", where)
        existing = ltm_collection.get(where=where)
        self._logger.debug("existing results: ids=%s", existing.get('ids'))
        content_hash = self._content_hash(content)
        self._logger.debug("content_hash computed: %s", content_hash)
        embedding = self._embedder.embed(content)
        self._logger.debug("embedding computed: len=%s", len(embedding))
        metadata = {
            "user_id": user_id,
            "server_id": server_id,
            "title": title,
            "category": category,
            "content_hash": content_hash,
            "created_at": datetime.utcnow().isoformat(),
        }
        if source:
            metadata["source"] = source
        if confidence is not None:
            metadata["confidence"] = confidence
        self._logger.debug("metadata prepared: %s", metadata)

        if existing.get("ids"):
            entry_id = existing["ids"][0]
            self._logger.debug("updating existing entry_id: %s", entry_id)
            ltm_collection.update(
                ids=[entry_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
            )
            self._logger.info("LTM fact updated: title='%s', content='%s...', category='%s', source='%s', confidence=%s", title, content[:50], category, source or 'manual', confidence)
            return entry_id

        entry_id = self._generate_id(user_id, server_id, prefix="ltm")
        self._logger.debug("creating new entry_id: %s", entry_id)
        ltm_collection.add(
            ids=[entry_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
        )
        self._logger.info("LTM fact created: title='%s', content='%s...', category='%s', source='%s', confidence=%s", title, content[:50], category, source or 'manual', confidence)
        return entry_id

    async def add_document(self, user_id: int, server_id: int, text_clair: str, text_embed: str) -> bool:
        _, ltm_collection = self._require_collections()
        self._logger.debug("add_document: user_id=%s, server_id=%s, text_clair=%s..., text_embed=%s...", user_id, server_id, text_clair[:50], text_embed[:50])
        content_hash = self._content_hash(text_embed)
        self._logger.debug("content_hash for text_embed: %s", content_hash)
        # pre-check exact duplicate via content_hash
        base_where = self._build_where_clause(user_id, server_id)
        if isinstance(base_where, dict) and "$and" in base_where:
            where = {"$and": base_where["$and"] + [{"content_hash": {"$eq": content_hash}}]}
        else:
            where = {"$and": [base_where, {"content_hash": {"$eq": content_hash}}]}
        exists = ltm_collection.get(where=where)
        self._logger.debug("duplicate check: exists ids=%s", exists.get('ids'))
        if exists.get("ids"):
            self._logger.debug("Document skipped (exact duplicate hash)")
            self._logger.info("Document skipped (exact duplicate hash)")
            return False
        embedding = self._embedder.embed(text_embed)
        self._logger.debug("embedding computed for text_embed: len=%s", len(embedding))
        results = ltm_collection.query(
            query_embeddings=[embedding],
            where=self._build_where_clause(user_id, server_id),
            n_results=3,
            include=["metadatas", "documents", "distances"],
        )
        distances = results.get("distances") or []
        self._logger.debug("similarity query results: distances=%s", distances)
        if distances and distances[0]:
            min_distance = min(distances[0])
            self._logger.debug("min_distance=%s, LTM_MIN_SIMILARITY=%s", min_distance, LTM_MIN_SIMILARITY)
            if min_distance < LTM_MIN_SIMILARITY:
                self._logger.debug("Document skipped (redundant, distance too low)")
                self._logger.info("Document skipped (redundant, distance=%.3f)", min_distance)
                return False

        self._logger.debug("Calling add_long_term_memory for document")
        await self.add_long_term_memory(
            user_id,
            server_id,
            title=text_clair[:100],
            content=text_embed,
            category="document",
        )
        self._logger.info("Document stored in LTM for user=%s", user_id)
        return True

    async def add_memory(self, user_id: int, server_id: int, text_to_embed: str) -> str:
        return await self.add_conversation_message(user_id, server_id, text_to_embed, role="system")

    async def get_memories(self, user_id: int, server_id: int, limit_stm: int = 5, limit_ltm: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        stm_collection, ltm_collection = self._require_collections()
        await self._delete_old_stm_memories(user_id, server_id)
        where_clause = self._build_where_clause(user_id, server_id)

        stm_results = stm_collection.get(
            where=where_clause,
            limit=limit_stm,
            include=["metadatas", "documents"],
        )
        ltm_results = ltm_collection.get(
            where=where_clause,
            limit=limit_ltm,
            include=["metadatas", "documents"],
        )

        memories: Dict[str, List[Dict[str, Any]]] = {"stm": [], "ltm": []}

        for idx, entry_id in enumerate(stm_results.get("ids", [])):
            meta = stm_results.get("metadatas", [])[idx]
            memories["stm"].append(
                {
                    "id": entry_id,
                    "text": stm_results.get("documents", [])[idx],
                    "role": meta.get("role"),
                    "created_at": meta.get("created_at"),
                }
            )

        for idx, entry_id in enumerate(ltm_results.get("ids", [])):
            meta = ltm_results.get("metadatas", [])[idx]
            memories["ltm"].append(
                {
                    "id": entry_id,
                    "title": meta.get("title"),
                    "content": ltm_results.get("documents", [])[idx],
                    "category": meta.get("category"),
                    "created_at": meta.get("created_at"),
                }
            )

        return memories

    async def get_long_term_memories(self, user_id: int, server_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        _, ltm_collection = self._require_collections()
        results = ltm_collection.get(
            where=self._build_where_clause(user_id, server_id),
            limit=limit,
            include=["metadatas", "documents"],
        )

        memories: List[Dict[str, Any]] = []
        for idx, entry_id in enumerate(results.get("ids", [])):
            meta = results.get("metadatas", [])[idx]
            memories.append(
                {
                    "id": entry_id,
                    "title": meta.get("title"),
                    "content": results.get("documents", [])[idx],
                    "category": meta.get("category"),
                    "created_at": meta.get("created_at"),
                }
            )
        return memories

    async def search_memories(
        self,
        user_id: int,
        server_id: int,
        query: str,
        limit: int = 5,
        memory_type: str = "both",
    ) -> Dict[str, List[Dict[str, Any]]]:
        stm_collection, ltm_collection = self._require_collections()
        embedding = self._embedder.embed(query)
        result: Dict[str, List[Dict[str, Any]]] = {"stm": [], "ltm": []}

        if memory_type in {"stm", "both"}:
            stm_results = stm_collection.query(
                query_embeddings=[embedding],
                where=self._build_where_clause(user_id, server_id),
                n_results=limit,
                include=["metadatas", "documents"],
            )
            ids = list(stm_results.get("ids", [[]])[0])
            docs = stm_results.get("documents", [[]])[0]
            metas = stm_results.get("metadatas", [[]])[0]
            for idx, entry_id in enumerate(ids):
                result["stm"].append(
                    {
                        "id": entry_id,
                        "text": docs[idx],
                        "role": metas[idx].get("role"),
                        "created_at": metas[idx].get("created_at"),
                    }
                )

        if memory_type in {"ltm", "both"}:
            ltm_results = ltm_collection.query(
                query_embeddings=[embedding],
                where=self._build_where_clause(user_id, server_id),
                n_results=limit,
                include=["metadatas", "documents"],
            )
            ids = list(ltm_results.get("ids", [[]])[0])
            docs = ltm_results.get("documents", [[]])[0]
            metas = ltm_results.get("metadatas", [[]])[0]
            for idx, entry_id in enumerate(ids):
                result["ltm"].append(
                    {
                        "id": entry_id,
                        "title": metas[idx].get("title"),
                        "content": docs[idx],
                        "category": metas[idx].get("category"),
                        "created_at": metas[idx].get("created_at"),
                    }
                )

        return result

    async def get_hybrid_memories(
        self,
        user_id: int,
        server_id: int,
        current_query: str,
        recent_limit: int = 3,
        similar_limit: int = 5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        stm_collection, ltm_collection = self._require_collections()
        await self._delete_old_stm_memories(user_id, server_id)
        hybrids: Dict[str, List[Dict[str, Any]]] = {"stm": [], "ltm": []}
        where_clause = self._build_where_clause(user_id, server_id)

        stm_results = stm_collection.get(
            where=where_clause,
            limit=recent_limit,
            include=["metadatas", "documents"],
        )
        ids = list(stm_results.get("ids", []))
        for idx, entry_id in enumerate(ids):
            meta = stm_results.get("metadatas", [])[idx]
            hybrids["stm"].append(
                {
                    "id": entry_id,
                    "text": stm_results.get("documents", [])[idx],
                    "role": meta.get("role"),
                    "created_at": meta.get("created_at"),
                }
            )

        embedding = self._embedder.embed(current_query)
        ltm_results = ltm_collection.query(
            query_embeddings=[embedding],
            where=where_clause,
            n_results=similar_limit,
            include=["metadatas", "documents"],
        )
        ids = list(ltm_results.get("ids", [[]])[0])
        docs = ltm_results.get("documents", [[]])[0]
        metas = ltm_results.get("metadatas", [[]])[0]
        for idx, entry_id in enumerate(ids):
            hybrids["ltm"].append(
                {
                    "id": entry_id,
                    "title": metas[idx].get("title"),
                    "content": docs[idx],
                    "category": metas[idx].get("category"),
                    "created_at": metas[idx].get("created_at"),
                }
            )

        return hybrids

    async def clear_history(self, user_id: int, server_id: Optional[int] = None, memory_type: str = "stm") -> int:
        stm_collection, ltm_collection = self._require_collections()
        where_clause = self._build_where_clause(user_id, server_id)
        deleted = 0

        if memory_type in {"stm", "both"}:
            stm_ids = stm_collection.get(where=where_clause).get("ids", [])
            if stm_ids:
                stm_collection.delete(ids=stm_ids)
                deleted += len(stm_ids)

        if memory_type in {"ltm", "both"}:
            ltm_ids = ltm_collection.get(where=where_clause).get("ids", [])
            if ltm_ids:
                ltm_collection.delete(ids=ltm_ids)
                deleted += len(ltm_ids)

        self._logger.info("Cleared %s memory entries for user=%s", deleted, user_id)
        return deleted

    async def delete_stm_memories(self, ids: List[str]) -> None:
        stm_collection, _ = self._require_collections()
        stm_collection.delete(ids=ids)
        self._logger.info("Deleted %s STM memories", len(ids))