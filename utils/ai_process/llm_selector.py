import logging
import asyncio
from config import LOGGER_NAME, MEGALLM_API_KEY, OPENROUTER_API_KEY, IO_INTELLIGENCE_API_KEY, LLM_SELECTOR_PREPROMPT, AVAILABLE_MODELS as MODELS
from dotenv import load_dotenv
import os
import requests

logger = logging.getLogger(LOGGER_NAME)

load_dotenv()

class LLMSelector:
    def __init__(self):
        pass

    async def _megallm_llm_selector(self, messages: list) -> str:
        def _sync_request():
            response = requests.post(
                "https://api.megallm.com/v1/chat/completions",
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
                raise Exception(f"Megallm API error: {response.status_code} {response.text}")
        
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
                raise Exception(f"IO Intelligence API error: {response.status_code} {response.text}")
        
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
                raise Exception(f"OpenRouter API error: {response.status_code} {response.text}")
        
        return await asyncio.to_thread(_sync_request)

    async def select_model(self, input: str) -> str:
        messages = [
            {"role": "system", "content": LLM_SELECTOR_PREPROMPT},
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
        for model_name in MODELS:
            if model_name.lower() in t:
                return model_name
        return "llama"
    