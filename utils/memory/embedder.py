"""Embedder implementation using FastEmbed with advanced caching."""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import time
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastembed import TextEmbedding

from config import EMBEDDER_CACHE_DIR, EMBEDDER_MODEL, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
CACHE_DIR = Path(EMBEDDER_CACHE_DIR)


class TextEmbedder:
    """FastEmbed wrapper with persistent LRU cache and memory management."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        enable_cache: bool = True,
        max_cache_size: int = 10000,
        cache_ttl_hours: int = 24,
    ) -> None:
        self._logger = logging.getLogger(LOGGER_NAME)
        self.model_name = model_name or EMBEDDER_MODEL
        self.enable_cache = enable_cache
        self.max_cache_size = max_cache_size
        self.cache_ttl_seconds = cache_ttl_hours * 3600

        self._embedder: Optional[TextEmbedding] = None
        self._memory_cache: OrderedDict[str, Tuple[List[float], float]] = (
            OrderedDict()
        )  # (embedding, timestamp)
        self._cache_dir = CACHE_DIR
        self._cache_index_file = self._cache_dir / "cache_index.json"
        self._cache_data_dir = self._cache_dir / "embeddings"

        # Defer initialization to async method
        # self._ensure_initialized()

    async def initialize(self) -> None:
        """Async initialize embedder and load persistent cache."""
        if self._embedder is not None:
            return

        # Create cache directories
        self._cache_data_dir.mkdir(parents=True, exist_ok=True)
        load_start = time.time()
        # Initialize embedder
        self._embedder = await asyncio.to_thread(
            TextEmbedding, model_name=self.model_name, cache_dir=str(self._cache_dir)
        )
        load_time = time.time() - load_start
        self._logger.info(
            f"FastEmbed model {self.model_name} loaded in {load_time:.4f}s"
        )

        # Load persistent cache index
        if self.enable_cache:
            self._load_cache_index()

    def _load_cache_index(self) -> None:
        """Load cache index from disk."""
        try:
            if self._cache_index_file.exists():
                with open(self._cache_index_file, "r") as f:
                    index_data = json.load(f)

                current_time = time.time()
                valid_entries = {}

                # Load only non-expired entries
                for key, timestamp in index_data.items():
                    if current_time - timestamp < self.cache_ttl_seconds:
                        valid_entries[key] = timestamp

                # Keep only recent entries if too many
                if len(valid_entries) > self.max_cache_size:
                    sorted_entries = sorted(
                        valid_entries.items(), key=lambda x: x[1], reverse=True
                    )
                    valid_entries = dict(sorted_entries[: self.max_cache_size])

                self._logger.debug(
                    f"Loaded {len(valid_entries)} cached embeddings from disk"
                )
        except Exception as e:
            self._logger.warning(f"Failed to load cache index: {e}")

    def _save_cache_index(self) -> None:
        """Save cache index to disk."""
        try:
            index_data = {
                key: timestamp for key, (_, timestamp) in self._memory_cache.items()
            }
            with open(self._cache_index_file, "w") as f:
                json.dump(index_data, f)
        except Exception as e:
            self._logger.warning(f"Failed to save cache index: {e}")

    def _get_embedding_from_disk(self, cache_key: str) -> Optional[List[float]]:
        """Load embedding from disk cache."""
        cache_file = self._cache_data_dir / f"{cache_key}.pkl"
        try:
            if cache_file.exists():
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
        except Exception as e:
            self._logger.warning(f"Failed to load cached embedding {cache_key}: {e}")
        return None

    def _save_embedding_to_disk(self, cache_key: str, embedding: List[float]) -> None:
        """Save embedding to disk cache."""
        cache_file = self._cache_data_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(embedding, f)
        except Exception as e:
            self._logger.warning(f"Failed to save embedding {cache_key}: {e}")

    def _cleanup_old_cache_files(self) -> None:
        """Remove old cache files that are no longer in index."""
        try:
            current_keys = set(self._memory_cache.keys())
            for cache_file in self._cache_data_dir.glob("*.pkl"):
                key = cache_file.stem
                if key not in current_keys:
                    cache_file.unlink()
        except Exception as e:
            self._logger.warning(f"Failed to cleanup old cache files: {e}")

    @staticmethod
    def _cache_key(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def embed(self, text: str) -> List[float]:
        """Embed text with caching."""
        if not self.enable_cache:
            assert self._embedder is not None
            return list(self._embedder.embed([text]))[0].tolist()

        cache_key = self._cache_key(text)
        current_time = time.time()

        # Check memory cache first
        if cache_key in self._memory_cache:
            embedding, timestamp = self._memory_cache[cache_key]
            if current_time - timestamp < self.cache_ttl_seconds:
                # Move to end (most recently used)
                self._memory_cache.move_to_end(cache_key)
                return embedding
            else:
                # Expired, remove from memory
                del self._memory_cache[cache_key]

        # Check disk cache
        embedding = self._get_embedding_from_disk(cache_key)
        if embedding is not None:
            # Add to memory cache
            self._memory_cache[cache_key] = (embedding, current_time)
            self._memory_cache.move_to_end(cache_key)
            self._logger.debug(f"Disk cache hit for text of length {len(text)}")
            return embedding

        # Generate new embedding
        assert self._embedder is not None
        embedding = list(self._embedder.embed([text]))[0].tolist()

        # Add to caches
        self._memory_cache[cache_key] = (embedding, current_time)
        self._memory_cache.move_to_end(cache_key)
        self._save_embedding_to_disk(cache_key, embedding)

        # Maintain cache size limits
        if len(self._memory_cache) > self.max_cache_size:
            # Remove oldest (least recently used)
            oldest_key, _ = self._memory_cache.popitem(last=False)
            self._logger.debug(f"Removed old cache entry: {oldest_key}")

        # Periodically save index and cleanup
        if len(self._memory_cache) % 100 == 0:
            self._save_cache_index()
            self._cleanup_old_cache_files()

        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed batch of texts with caching."""
        if not self.enable_cache:
            assert self._embedder is not None
            return [v.tolist() for v in list(self._embedder.embed(texts))]

        results: List[List[float]] = []
        uncached_texts: List[str] = []
        uncached_indices: List[int] = []
        current_time = time.time()

        # Check cache for each text
        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)

            # Check memory cache
            if cache_key in self._memory_cache:
                embedding, timestamp = self._memory_cache[cache_key]
                if current_time - timestamp < self.cache_ttl_seconds:
                    results.append(embedding)
                    self._memory_cache.move_to_end(cache_key)
                    continue

            # Check disk cache
            embedding = self._get_embedding_from_disk(cache_key)
            if embedding is not None:
                results.append(embedding)
                self._memory_cache[cache_key] = (embedding, current_time)
                self._memory_cache.move_to_end(cache_key)
                continue

            # Not cached
            results.append([])
            uncached_texts.append(text)
            uncached_indices.append(i)

        # Generate embeddings for uncached texts
        if uncached_texts:
            assert self._embedder is not None
            generated = [v.tolist() for v in list(self._embedder.embed(uncached_texts))]

            for idx, (text_idx, embedding) in enumerate(
                zip(uncached_indices, generated)
            ):
                results[text_idx] = embedding
                cache_key = self._cache_key(uncached_texts[idx])

                # Add to caches
                self._memory_cache[cache_key] = (embedding, current_time)
                self._memory_cache.move_to_end(cache_key)
                self._save_embedding_to_disk(cache_key, embedding)

        # Maintain cache size
        while len(self._memory_cache) > self.max_cache_size:
            oldest_key, _ = self._memory_cache.popitem(last=False)

        # Periodic maintenance
        if len(self._memory_cache) % 100 == 0:
            self._save_cache_index()
            self._cleanup_old_cache_files()

        return results

    def clear_cache(self) -> int:
        """Clear memory cache and optionally disk cache."""
        count = len(self._memory_cache)
        self._memory_cache.clear()

        # Remove cache files
        try:
            import shutil

            if self._cache_data_dir.exists():
                shutil.rmtree(self._cache_data_dir)
                self._cache_data_dir.mkdir()

            if self._cache_index_file.exists():
                self._cache_index_file.unlink()

        except Exception as e:
            self._logger.warning(f"Failed to clear disk cache: {e}")

        self._logger.info(f"Cleared embedding cache ({count} memory entries)")
        return count

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        try:
            disk_files = (
                len(list(self._cache_data_dir.glob("*.pkl")))
                if self._cache_data_dir.exists()
                else 0
            )
        except Exception:
            disk_files = 0

        return {
            "memory_entries": len(self._memory_cache),
            "disk_entries": disk_files,
            "max_cache_size": self.max_cache_size,
            "enabled": int(self.enable_cache),
        }
