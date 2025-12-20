import asyncio
import logging
import os

import requests
from dotenv import load_dotenv

from config import AVAILABLE_MODELS, MODELS, read_file
from config import (IO_INTELLIGENCE_API_KEY,
                    LOGGER_NAME, MEGALLM_API_KEY, OPENROUTER_API_KEY)

logger = logging.getLogger(LOGGER_NAME)

llm_selector_prompt = read_file("configs/prompts/llm_selector.txt")
models_str = ""
for model in MODELS:
    models_str += f"- **{model['name']}**: {model['description']}\n"
llm_selector_prompt = llm_selector_prompt.format(models=models_str)

load_dotenv()

class LLMSelector:
    def __init__(self):
        pass

    async def _megallm_llm_selector(self, messages: list) -> str:
        def _sync_request():
            response = requests.post(
                "https://ai.megallm.io/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {MEGALLM_API_KEY}"
                },
                json={
                    "model": "openai-gpt-oss-20b",
                    "messages": messages
                }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"Megallm API error: {response.status_code} {response.text}")
        
        return await asyncio.to_thread(_sync_request)

    async def _io_intelligence_llm(self, messages: list) -> str:
        def _sync_request():
            response = requests.post(
                "https://api.intelligence.io.solutions/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {IO_INTELLIGENCE_API_KEY}"
                },
                json={
                    "model": "openai/gpt-oss-20b",
                    "messages": messages
                    }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"IO Intelligence API error: {response.status_code} {response.text}")
        
        return await asyncio.to_thread(_sync_request)

    async def _openrouter_llm_selector(self, messages: list) -> str:
        def _sync_request():
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}"
                },
                json={
                    "model": "openai/gpt-oss-20b",
                    "messages": messages
                }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenRouter API error: {response.status_code} {response.text}")
        
        return await asyncio.to_thread(_sync_request)

    async def select_model(self, input: str) -> str:
        messages = [
            {"role": "system", "content": llm_selector_prompt},
            {"role": "user", "content": input}
        ]

        try:
            text = await self._megallm_llm_selector(messages)
        except Exception as e:
            logger.error(f"Megallm LLM Selector failed: {e}. Falling back to OpenRouter LLM Selector.")
            try:
                text = await self._openrouter_llm_selector(messages)
            except Exception as e2:
                logger.error(f"OpenRouter LLM Selector failed: {e2}. Falling back to IO Intelligence LLM Selector.")
                try:
                    text = await self._io_intelligence_llm(messages)
                except Exception as e3:
                    logger.error(f"IO Intelligence LLM Selector also failed: {e3}. Using default model.")
                    return "cerebras/llama3.3-70b"
        
        model = self._parse_llm_selection(text)
        return model

    def _parse_llm_selection(self, text: str) -> str:
        t = text.lower()
        for model_name in AVAILABLE_MODELS:
            if model_name.lower() in t:
                return model_name
        return "llama"
    