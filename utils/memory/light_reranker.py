"""Light reranker using ONNX for local cross-encoder reranking."""

import asyncio
import logging
import time
from typing import List

from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer

from config import LOGGER_NAME, RERANKER_CACHE_DIR, RERANKER_MODEL

logger = logging.getLogger(LOGGER_NAME)


class LightReranker:
    """ONNX-based cross-encoder reranker for refining search results."""

    def __init__(self, model_name: str = None):
        self.model_name = (
            model_name or RERANKER_MODEL or "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )
        self.cache_dir = RERANKER_CACHE_DIR
        self.model = None
        self.tokenizer = None
        # Defer loading to async initialize

    async def initialize(self):
        """Async load the ONNX model and tokenizer."""
        if self.model is not None:
            return
        try:
            load_start = time.time()
            self.model = await asyncio.to_thread(
                ORTModelForSequenceClassification.from_pretrained,
                self.model_name,
                export=False,
                cache_dir=self.cache_dir,
            )
            self.tokenizer = await asyncio.to_thread(
                AutoTokenizer.from_pretrained, self.model_name, cache_dir=self.cache_dir
            )
            load_time = time.time() - load_start
            logger.info(
                f"LightReranker loaded model: {self.model_name} in {load_time:.4f}s"
            )
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            raise

    def rerank(self, query: str, candidates: List[str], top_k: int = 5) -> List[str]:
        """Rerank candidates based on relevance to query.

        Args:
            query: The search query.
            candidates: List of candidate texts.
            top_k: Number of top results to return.

        Returns:
            List of reranked candidate texts.
        """
        if not candidates:
            return []

        # Prepare inputs
        inputs = [f"{query} [SEP] {candidate}" for candidate in candidates]

        # Tokenize
        tokenized = self.tokenizer(
            inputs, return_tensors="pt", padding=True, truncation=True, max_length=512
        )

        # Predict scores
        outputs = self.model(**tokenized)
        scores = (
            outputs.logits.squeeze().tolist()
        )  # Assuming single logit for similarity
        if isinstance(scores, float):
            scores = [scores]

        # Sort by score descending
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

        # Return top_k
        return [item[0] for item in ranked[:top_k]]
