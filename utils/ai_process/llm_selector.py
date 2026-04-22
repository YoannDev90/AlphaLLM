import json
import logging
import os
import random
from typing import Optional

import litellm

from config import AVAILABLE_MODELS, LOGGER_NAME, MODELS, read_file

logger = logging.getLogger(LOGGER_NAME)

llm_selector_prompt = read_file("configs/prompts/llm_selector.txt")
models_str = ""
for name, desc in MODELS.items():
    models_str += f"- **{name}**: {desc}\n"
llm_selector_prompt = llm_selector_prompt.format(models=models_str)


class LLMSelector:
    def __init__(self):
        self.config_path = "configs/misc/llm_selector.json"

    def _load_configs(self):
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load llm_selector configs: {e}")
            return []

    async def select_model(self, input_text: str) -> str:
        configs = self._load_configs()
        if not configs:
            return "llama"

        messages = [
            {"role": "system", "content": llm_selector_prompt},
            {"role": "user", "content": input_text},
        ]

        random.shuffle(configs)

        for config in configs:
            params = config.get("litellm_params", {})
            model = params.get("model")
            api_key = os.getenv(params.get("api_key", ""))

            if not api_key:
                continue

            try:
                logger.debug(f"Trying LLM selector with model: {model}")
                response = await litellm.acompletion(
                    model=model,
                    api_key=api_key,
                    messages=messages,
                    temperature=0.3,
                    timeout=10,
                )
                text = response.choices[0].message.content
                selected = self._parse_llm_selection(text)
                if selected:
                    logger.info(f"LLMSelector chose: {selected} (via {model})")
                    return selected
            except Exception as e:
                logger.warning(f"Selector model {model} failed: {e}")
                continue

        logger.error("All LLM selectors failed. Using default model.")
        return "llama"

    def _parse_llm_selection(self, text: Optional[str]) -> Optional[str]:
        if text is None:
            return None
        t = text.lower()
        for model_name in AVAILABLE_MODELS:
            if model_name.lower() in t:
                return model_name
        return None
