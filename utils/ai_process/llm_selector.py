import logging
import random
from typing import Optional

from config import AVAILABLE_MODELS, LOGGER_NAME, MODELS, read_file
from utils.ai_process.base_chat_model import ChatParameters
from utils.ai_process.chat_model import ChatModel

logger = logging.getLogger(LOGGER_NAME)

llm_selector_prompt = read_file("configs/prompts/llm_selector.txt")
models_str = ""
for name, desc in MODELS.items():
    models_str += f"- **{name}**: {desc}\n"
llm_selector_prompt = llm_selector_prompt.format(models=models_str)


class LLMSelector:
    def __init__(self):
        self.model = ChatModel("llm_selector")
        self.model.config_path = "configs/misc/llm_selector.json"

    async def select_model(self, input_text: str) -> str:
        messages = [
            {"role": "system", "content": llm_selector_prompt},
            {"role": "user", "content": input_text},
        ]

        logger.debug("Attempting to select model via LLMSelector...")
        try:
            params = ChatParameters(
                messages=messages,
                model="llm_selector",
                temperature=0.3,
            )
            result = await self.model.chat(params)
            selected = self._parse_llm_selection(result.response)
            if selected:
                logger.info(f"LLMSelector chose: {selected}")
                return selected
        except Exception as e:
            logger.error(f"LLMSelector failed: {e}")

        logger.error("LLM selection failed. Using default model.")
        return "llama"

    def _parse_llm_selection(self, text: Optional[str]) -> Optional[str]:
        if text is None:
            return None
        t = text.lower()
        for model_name in AVAILABLE_MODELS:
            if model_name.lower() in t:
                return model_name
        return None
