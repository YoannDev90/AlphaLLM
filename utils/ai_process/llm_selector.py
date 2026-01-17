import asyncio
import logging
import os
import random

import requests
from dotenv import load_dotenv
import litellm

from config import (AVAILABLE_MODELS, MODELS,LOGGER_NAME,read_file, 
                    MEGALLM_API_KEY, 
                    OPENROUTER_API_KEY, 
                    LLM7_API_KEY,
                    LLM_GATEWAY_API_KEY,
                    MAPLE_AI_API_KEY,
                    ZANITY_API_KEY
                    )

logger = logging.getLogger(LOGGER_NAME)

llm_selector_prompt = read_file("configs/prompts/llm_selector.txt")
models_str = ""
for name, desc in MODELS.items():
    models_str += f"- **{name}**: {desc}\n"
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
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"Megallm API error: {response.status_code} {response.text}")
        
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
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenRouter API error: {response.status_code} {response.text}")
        
        return await asyncio.to_thread(_sync_request)
    
    async def _llm_gateway_llm_selector(self, messages: list) -> str:
        try:
            return litellm.completion(
                model="openai/gpt-oss-20b",
                base_url="https://api.llmgateway.io/v1",
                api_key=LLM_GATEWAY_API_KEY,
                messages=messages,
                timeout=15
            ).choices[0].message.content
        except Exception as e:
            logger.error(f"LLM Gateway API error: {e}")

    async def _llm7_llm_selector(self, messages: list) -> str:
        try:
            return litellm.completion(
                model="openai/gemini-2.5-flash-lite",
                base_url="https://api.llm7.io/v1",
                api_key=LLM7_API_KEY,
                messages=messages,
                timeout=15
            ).choices[0].message.content
        except Exception as e:
            logger.error(f"LLM7 API error: {e}")

    async def _zanity_llm_selector(self, messages: list) -> str:
        try:
            return litellm.completion(
                model="openai/llama-3.1-8b-instruct",
                base_url="https://api.zanity.xyz/v1",
                api_key=ZANITY_API_KEY,
                messages=messages,
                timeout=15
            ).choices[0].message.content
        except Exception as e:
            logger.error(f"Zanity API error: {e}")

    async def _maple_ai_llm_selector(self, messages: list) -> str:
        try:
            return litellm.completion(
                model="openai/gpt-oss-20b",
                base_url="https://api.mapleai.de/v1",
                api_key=MAPLE_AI_API_KEY,
                messages=messages,
                timeout=15
            ).choices[0].message.content
        except Exception as e:
            logger.error(f"Maple AI API error: {e}")

    async def select_model(self, input: str) -> str:
        messages = [
            {"role": "system", "content": llm_selector_prompt},
            {"role": "user", "content": input}
        ]

        selectors = [
            self._megallm_llm_selector,
            self._openrouter_llm_selector,
            self._llm_gateway_llm_selector,
            self._llm7_llm_selector,
            self._zanity_llm_selector,
            self._maple_ai_llm_selector
        ]
        random.shuffle(selectors)

        for selector in selectors:
            try:
                logger.debug(f"Trying LLM selector: {selector.__name__}")
                text = await selector(messages)
                logger.debug(f"{selector.__name__} response: {text}")
                model = self._parse_llm_selection(text)
                if model is not None:
                    return model
            except Exception as e:
                logger.error(f"{selector.__name__} failed: {e}")
                continue

        logger.error("All LLM selectors failed. Using default model.")
        return "llama"

    def _parse_llm_selection(self, text: str) -> str:
        if text is None:
            return None
        t = text.lower()
        for model_name in AVAILABLE_MODELS:
            if model_name.lower() in t:
                return model_name
        return None
    