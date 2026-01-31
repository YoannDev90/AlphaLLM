"""Light reranker using ONNX for local cross-encoder reranking."""

import logging
from typing import List

from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class LightReranker:
    """ONNX-based cross-encoder reranker for refining search results."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        """Load the ONNX model and tokenizer."""
        try:
            self.model = ORTModelForSequenceClassification.from_pretrained(
                self.model_name, export=False  # Already ONNX
            )
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            logger.info(f"LightReranker loaded model: {self.model_name}")
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
