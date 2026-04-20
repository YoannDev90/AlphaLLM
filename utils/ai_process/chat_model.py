import asyncio
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List

import litellm
from langfuse import get_client

from config import LOGGER_NAME
from utils.ai_process.base_chat_model import (BaseChatModel, ChatParameters,
                                              ChatResult)

logger = logging.getLogger(LOGGER_NAME)


class ChatModel(BaseChatModel):
    """Classe globale pour gérer tous les modèles de chat avec fallbacks (Non-Streaming)"""

    def __init__(self, model_name: str):
        """
        Initialise le modèle de chat

        Args:
            model_name: Nom du modèle (ex: "claude", "openai", etc.)
        """
        config_path = f"configs/text_models/{model_name}.json"
        super().__init__(config_path)
        self.model_name = model_name

    def _process_perplexity_citations(self, response_text: str, response) -> str:
        """ Traite les citations pour les réponses Perplexity """
        if self.model_name != "sonar":
            return response_text

        sources = (
            response.citations
            if hasattr(response, "citations") and response.citations
            else []
        )

        if not sources:
            return response_text

        def replace_citation(match):
            citation_num = int(match.group(1))
            if 1 <= citation_num <= len(sources):
                return f" [[{citation_num}]](<{sources[citation_num - 1]}>)"
            return match.group(0)

        processed_text = re.sub(r"\[(\d+)\]", replace_citation, response_text)
        return processed_text

    async def _non_stream_chat(
        self, parameters: ChatParameters, start_time: datetime, retry_count: int = 0
    ) -> ChatResult:
        """Chat non-streaming avec fallbacks"""
        configs = self._load_configs()
        
        if retry_count > 0:
            configs = configs[retry_count:] + configs[:retry_count]

        with get_client().start_as_current_observation(
            as_type="generation", name=f"user-completion-{datetime.now().isoformat()}"
        ) as gen:
            gen.update(input=parameters.messages)

            primary_config = configs[0]["litellm_params"]
            fallback_configs = [config["litellm_params"] for config in configs[1:]]

            params = {
                "model": primary_config["model"],
                "api_key": os.getenv(primary_config["api_key"]),
                "messages": parameters.messages,
                "drop_params": True,
                "timeout": 30.0,
            }

            if not params["api_key"]:
                if retry_count < len(configs) - 1:
                    return await self._non_stream_chat(parameters, start_time, retry_count + 1)
                return ChatResult(
                    response="API configuration error. Please check your API keys.",
                    usage=0,
                    model=parameters.model,
                    elapsed_time=self._format_elapsed_time(start_time),
                )

            if "api_base" in primary_config:
                params["api_base"] = primary_config["api_base"]

            fallbacks = []
            for fb_config in fallback_configs:
                api_key = os.getenv(fb_config["api_key"])
                if api_key:
                    fb_params = {"model": fb_config["model"], "api_key": api_key}
                    if "api_base" in fb_config:
                        fb_params["api_base"] = fb_config["api_base"]
                    fallbacks.append(fb_params)

            models_to_try = [params.copy()]
            for fb in fallbacks:
                fb_full = params.copy()
                fb_full.update(fb)
                models_to_try.append(fb_full)

            response = None
            for attempt_params in models_to_try:
                try:
                    response = await asyncio.wait_for(
                        litellm.acompletion(**attempt_params), timeout=30.0
                    )
                    break
                except Exception:
                    continue
            else:
                if retry_count < len(configs) - 1:
                    return await self._non_stream_chat(parameters, start_time, retry_count + 1)
                return ChatResult(
                    response="I'm sorry, but I couldn't generate a response due to an API error.",
                    usage=0,
                    model=parameters.model,
                    elapsed_time=self._format_elapsed_time(start_time),
                )

            usage = response.usage.total_tokens
            response_text = response.choices[0].message.content or ""
            response_text = self._process_perplexity_citations(response_text, response)
            response_text = self.clean_think_tags(response_text)

            gen.update(
                output=response_text,
                model=parameters.model,
                usage_details={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": usage,
                },
                model_parameters={"temperature": parameters.temperature, "stream": False},
            )

            return ChatResult(
                response=response_text,
                usage=usage,
                model=parameters.model,
                elapsed_time=self._format_elapsed_time(start_time),
            )

    async def chat(self, parameters: ChatParameters) -> ChatResult:
        """ Méthode principale (Non-Streaming) """
        start_time = datetime.now()
        return await self._non_stream_chat(parameters, start_time, 0)

    async def generate(self, parameters: ChatParameters):
        """ Générateur pour compatibilité """
        result = await self.chat(parameters)
        yield result
