"""Micro LLM handler for RAG synthesis."""
import json
import logging
from typing import List, Optional

import litellm

from config import POLLINATIONS_API_KEY, read_file


class MicroLLMHandler:
    """Handles micro LLM for RAG synthesis."""

    def __init__(self, config_path: str = "configs/misc/micro_llm.json"):
        self._logger = logging.getLogger(__name__)
        self._model_config = None
        self._synthesis_prompt = read_file("configs/prompts/rag_synthesis.txt")
        self._load_config(config_path)

    def _load_config(self, config_path: str):
        """Load micro LLM configuration."""
        try:
            with open(config_path, 'r') as f:
                configs = json.load(f)
                if configs and len(configs) > 0:
                    self._model_config = configs[0]  # Take first config
                    self._logger.info(f"Loaded micro LLM config: {self._model_config['model_name']}")
                else:
                    self._logger.warning("No micro LLM configs found")
        except Exception as e:
            self._logger.error(f"Failed to load micro LLM config: {e}")

    async def synthesize_memories(self, query: str, memories: List[str], max_tokens: int = 200) -> str:
        """Synthesize memories into a concise response using micro LLM."""
        if not self._model_config or not memories:
            return "\n".join(memories[:5])  # Fallback to raw memories

        try:
            # Prepare context from memories
            context = "\n".join(memories[:10])  # Use top 10 memories max

            prompt = self._synthesis_prompt.format(context=context, query=query)

            # Use litellm to call the micro LLM
            response = await litellm.acompletion(
                model=self._model_config["litellm_params"]["model"],
                api_base=self._model_config["litellm_params"]["api_base"],
                api_key=POLLICATIONS_API_KEY,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1  # Low temperature for factual responses
            )

            synthesized = response.choices[0].message.content.strip()
            self._logger.debug(f"Synthesized response: {synthesized[:100]}...")
            return synthesized

        except Exception as e:
            self._logger.error(f"Failed to synthesize with micro LLM: {e}")
            # Fallback to raw memories
            return "\n".join(memories[:5])