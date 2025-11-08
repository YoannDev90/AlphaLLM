"""Gestionnaire d'embeddings avec FastEmbed et cache"""

import logging
from typing import List, Optional, Dict
from fastembed import TextEmbedding
import os
from utils.config.app_config import EMBEDDER_MODEL
import hashlib

logger = logging.getLogger("AlphaLLM")


class TextEmbedder:
    """Classe pour gérer l'embedding de textes avec FastEmbed"""
    
    def __init__(self, model_name: str = EMBEDDER_MODEL, enable_cache: bool = True):
        """Initialise l'embedder avec le modèle spécifié
        
        Args:
            model_name: Nom du modèle FastEmbed à utiliser
            enable_cache: Activer le cache des embeddings
        """
        logger.debug(f"Initialisation de TextEmbedder avec le modèle: {model_name}")
        self.model_name = model_name
        self._embedder: Optional[TextEmbedding] = None
        self.cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models", "embedder")
        self.enable_cache = enable_cache
        self._embedding_cache: Dict[str, List[float]] = {}
        logger.debug(f"Répertoire cache défini: {self.cache_dir}")
        logger.debug(f"Cache embeddings: {enable_cache}")
    
    def _ensure_initialized(self) -> None:
        """S'assure que l'embedder est initialisé (lazy loading)"""
        if self._embedder is None:
            logger.debug(f"Initialisation lazy du modèle FastEmbed: {self.model_name}")
            os.makedirs(self.cache_dir, exist_ok=True)
            self._embedder = TextEmbedding(model_name=self.model_name, cache_dir=self.cache_dir)
            logger.debug("Embedder initialisé avec succès")
    
    def _get_cache_key(self, text: str) -> str:
        """Génère une clé de cache pour un texte
        
        Args:
            text: Texte à hasher
            
        Returns:
            Hash SHA256
        """
        return hashlib.sha256(text.encode()).hexdigest()
    
    def embed(self, text: str) -> List[float]:
        """Génère un embedding pour un texte avec cache
        
        Args:
            text: Le texte à embedder
            
        Returns:
            Liste de floats représentant l'embedding
            
        Raises:
            Exception: Si l'embedding échoue
        """
        logger.debug(f"Génération d'embedding pour texte de {len(text)} caractères")
        self._ensure_initialized()
        
        try:
            # Check cache
            if self.enable_cache:
                cache_key = self._get_cache_key(text)
                if cache_key in self._embedding_cache:
                    logger.debug("Embedding récupéré du cache")
                    return self._embedding_cache[cache_key]
            
            # Generate embedding
            embedding = list(self._embedder.embed([text]))[0].tolist()
            logger.debug(f"Embedding généré avec succès (dimension: {len(embedding)})")
            
            # Cache it
            if self.enable_cache:
                cache_key = self._get_cache_key(text)
                self._embedding_cache[cache_key] = embedding
                logger.debug(f"Embedding mis en cache ({len(self._embedding_cache)} entrées)")
            
            return embedding
        except Exception as e:
            logger.error(f"Erreur d'embedding: {str(e)}")
            logger.debug(f"Stack trace de l'erreur d'embedding: {e}", exc_info=True)
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Génère des embeddings pour plusieurs textes en batch avec cache
        
        Args:
            texts: Liste de textes à embedder
            
        Returns:
            Liste de listes de floats
            
        Raises:
            Exception: Si l'embedding échoue
        """
        logger.debug(f"Génération d'embeddings batch pour {len(texts)} textes")
        self._ensure_initialized()
        
        try:
            # Separate cached and uncached texts
            cache_keys = []
            uncached_texts = []
            uncached_indices = []
            
            if self.enable_cache:
                for i, text in enumerate(texts):
                    cache_key = self._get_cache_key(text)
                    cache_keys.append(cache_key)
                    if cache_key not in self._embedding_cache:
                        uncached_texts.append(text)
                        uncached_indices.append(i)
            else:
                uncached_texts = texts
                uncached_indices = list(range(len(texts)))
            
            logger.debug(f"Cache hit: {len(texts) - len(uncached_texts)}/{len(texts)}")
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                new_embeddings = [e.tolist() for e in self._embedder.embed(uncached_texts)]
                
                # Store in cache
                if self.enable_cache:
                    for idx, text in zip(uncached_indices, uncached_texts):
                        cache_key = cache_keys[idx]
                        self._embedding_cache[cache_key] = new_embeddings[uncached_indices.index(idx)]
                    logger.debug(f"Cache size: {len(self._embedding_cache)} embeddings")
            
            # Build result from cache + new
            result = []
            for i, text in enumerate(texts):
                if self.enable_cache and cache_keys[i] in self._embedding_cache:
                    result.append(self._embedding_cache[cache_keys[i]])
                elif not self.enable_cache and i in uncached_indices:
                    result.append(new_embeddings[uncached_indices.index(i)])
            
            logger.debug(f"Embeddings batch générés ({len(result)} embeddings de dimension {len(result[0]) if result else 0})")
            return result
        except Exception as e:
            logger.error(f"Erreur d'embedding batch: {str(e)}")
            logger.debug(f"Stack trace de l'erreur batch: {e}", exc_info=True)
            raise
    
    def clear_cache(self) -> int:
        """Vide le cache des embeddings
        
        Returns:
            Nombre d'entrées supprimées
        """
        count = len(self._embedding_cache)
        self._embedding_cache.clear()
        logger.info(f"Cache vidé: {count} entrées supprimées")
        return count
    
    def get_cache_stats(self) -> Dict:
        """Retourne les statistiques du cache
        
        Returns:
            Dictionnaire avec les stats
        """
        if not self._embedding_cache:
            return {"size": 0, "entries": 0, "enabled": self.enable_cache}
        
        # Estimate memory usage (each float is ~24 bytes, + overhead)
        sample_embedding = next(iter(self._embedding_cache.values())) if self._embedding_cache else []
        bytes_per_embedding = len(sample_embedding) * 24
        total_bytes = len(self._embedding_cache) * bytes_per_embedding
        
        return {
            "size": total_bytes,
            "size_mb": total_bytes / (1024 * 1024),
            "entries": len(self._embedding_cache),
            "enabled": self.enable_cache,
            "embedding_dim": len(sample_embedding) if sample_embedding else 0
        }
