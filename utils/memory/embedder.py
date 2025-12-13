"""Embedder implementation aligned with the refactor stack."""
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from fastembed import TextEmbedding

from config import EMBEDDER_CACHE_DIR, EMBEDDER_MODEL, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
CACHE_DIR = Path(EMBEDDER_CACHE_DIR)


class TextEmbedder:
    """FastEmbed wrapper with a simple in-memory cache and filesystem storage."""

    def __init__(self, model_name: Optional[str] = None, enable_cache: bool = True) -> None:
        self._logger = logging.getLogger(LOGGER_NAME)
        self.model_name = model_name or EMBEDDER_MODEL
        self.enable_cache = enable_cache
        self._embedder: Optional[TextEmbedding] = None
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_dir = CACHE_DIR
        self._logger.debug(f"Initializing TextEmbedder (model={self.model_name}, cache={self.enable_cache})")

    def _ensure_initialized(self) -> None:
        if self._embedder is not None:
            return
        os.makedirs(self._cache_dir, exist_ok=True)
        self._embedder = TextEmbedding(model_name=self.model_name, cache_dir=str(self._cache_dir))
        self._logger.debug(f"FastEmbed model {self.model_name} loaded")

    @staticmethod
    def _cache_key(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def embed(self, text: str) -> List[float]:
        self._ensure_initialized()
        cache_key = self._cache_key(text)
        if self.enable_cache and cache_key in self._embedding_cache:
            self._logger.debug(f"Cache hit for string of length {len(text)}")
            return self._embedding_cache[cache_key]

        assert self._embedder is not None
        embedding = list(self._embedder.embed([text]))[0].tolist()
        if self.enable_cache:
            self._embedding_cache[cache_key] = embedding
        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._ensure_initialized()
        assert self._embedder is not None

        results: List[List[float]] = []
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []
        cache_keys: List[str] = []

        for index, text in enumerate(texts):
            key = self._cache_key(text)
            cache_keys.append(key)
            if self.enable_cache and key in self._embedding_cache:
                results.append(self._embedding_cache[key])
            else:
                uncached_indices.append(index)
                uncached_texts.append(text)
                results.append([])

        if uncached_texts:
            generated = [v.tolist() for v in list(self._embedder.embed(uncached_texts))]
            for idx, embed in zip(uncached_indices, generated):
                results[idx] = embed
                if self.enable_cache:
                    self._embedding_cache[cache_keys[idx]] = embed

        return results

    def clear_cache(self) -> int:
        count = len(self._embedding_cache)
        self._embedding_cache.clear()
        self._logger.info(f"Cleared embedding cache ({count} entries)")
        return count

    def get_cache_stats(self) -> Dict[str, int]:
        return {
            "entries": len(self._embedding_cache),
            "enabled": int(self.enable_cache),
        }
