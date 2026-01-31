"""Faiss-based memory manager with local reranker."""

import logging
from typing import Dict, List, Optional

import faiss
import numpy as np

from config import LOGGER_NAME
from utils.memory.embedder import TextEmbedder
from utils.memory.light_reranker import LightReranker

logger = logging.getLogger(LOGGER_NAME)


class FaissMemoryManager:
    """Memory manager using Faiss for vector storage and ONNX reranker."""

    def __init__(self, embedder: Optional[TextEmbedder] = None, dimension: int = 384):
        self.embedder = embedder or TextEmbedder()
        self.dimension = dimension
        self.reranker = LightReranker()

        # Faiss index
        self.index = faiss.IndexHNSWFlat(dimension, 32)  # HNSW for efficiency
        self.metadata: List[Dict] = []  # Store metadata separately
        self.id_to_idx: Dict[str, int] = {}

        logger.info(f"FaissMemoryManager initialized with dimension {dimension}")

    async def initialize(self) -> None:
        """Async initialize embedder and reranker."""
        await self.embedder.initialize()
        await self.reranker.initialize()

    async def add_memory(self, id: str, text: str, metadata: Optional[Dict] = None):
        """Add a memory to Faiss."""
        try:
            embedding = self.embedder.embed(text)
            idx = len(self.metadata)
            self.index.add(np.array([embedding], dtype=np.float32))
            self.metadata.append({"id": id, "text": text, "metadata": metadata or {}})
            self.id_to_idx[id] = idx
            logger.debug(f"Added memory {id}")
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")

    async def search_memories(self, query: str, top_k: int = 20) -> List[str]:
        """Search and rerank memories."""
        try:
            query_emb = self.embedder.embed(query)
            distances, indices = self.index.search(
                np.array([query_emb], dtype=np.float32), top_k
            )

            candidates = []
            for i, idx in enumerate(indices[0]):
                if idx != -1:
                    candidates.append(self.metadata[idx]["text"])

            # Rerank
            reranked = self.reranker.rerank(query, candidates, top_k=top_k // 2)
            return reranked
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return []

    async def search_with_metadata(self, query: str, top_k: int = 20) -> List[Dict]:
        """Search and rerank memories with metadata."""
        try:
            query_emb = self.embedder.embed(query)
            distances, indices = self.index.search(
                np.array([query_emb], dtype=np.float32), top_k
            )

            candidates = []
            for i, idx in enumerate(indices[0]):
                if idx != -1:
                    item = self.metadata[idx]
                    candidates.append(
                        {
                            "text": item["text"],
                            "metadata": item["metadata"],
                            "distance": distances[0][i],
                        }
                    )

            # Rerank - assuming reranker returns indices or texts
            reranked_texts = self.reranker.rerank(
                query, [c["text"] for c in candidates], top_k=top_k // 2
            )
            # Match back to metadata
            result = []
            for text in reranked_texts:
                for c in candidates:
                    if c["text"] == text:
                        result.append(c)
                        break
            return result
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return []

    def get_by_metadata_filter(self, filter_func) -> List[Dict]:
        """Get items by metadata filter function."""
        return [item for item in self.metadata if filter_func(item["metadata"])]

    def delete_by_metadata_filter(self, filter_func) -> int:
        """Delete items by metadata filter function."""
        to_delete = []
        for i, item in enumerate(self.metadata):
            if filter_func(item["metadata"]):
                to_delete.append(i)

        # Rebuild index without deleted items
        if to_delete:
            new_metadata = []
            new_embeddings = []
            for i, item in enumerate(self.metadata):
                if i not in to_delete:
                    new_metadata.append(item)
                    emb = self.embedder.embed(item["text"])
                    new_embeddings.append(emb)

            self.metadata = new_metadata
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
            if new_embeddings:
                self.index.add(np.array(new_embeddings, dtype=np.float32))
            self.id_to_idx = {item["id"]: i for i, item in enumerate(self.metadata)}

        return len(to_delete)

    async def clear_memories(self):
        """Clear all memories."""
        self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        self.metadata = []
        self.id_to_idx = {}
        logger.info("Memories cleared")

    def save_index(self, path: str):
        """Save Faiss index."""
        faiss.write_index(self.index, path)

    def load_index(self, path: str):
        """Load Faiss index."""
        self.index = faiss.read_index(path)
