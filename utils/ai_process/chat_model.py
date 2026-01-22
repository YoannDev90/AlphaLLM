import logging
import os
import re
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Union

import litellm
from langfuse import get_client

from config import LOGGER_NAME
from utils.ai_process.base_chat_model import (BaseChatModel, ChatParameters,
                                              ChatResult, StreamChunk)

logger = logging.getLogger(LOGGER_NAME)

class ChatModel(BaseChatModel):
    """Classe globale pour gérer tous les modèles de chat avec streaming et fallbacks"""

    def __init__(self, model_name: str):
        """
        Initialise le modèle de chat

        Args:
            model_name: Nom du modèle (ex: "claude", "openai", etc.)
        """
        config_path = f"configs/text-models/{model_name}.json"
        super().__init__(config_path)
        self.model_name = model_name

    def _process_perplexity_citations(self, response_text: str, response) -> str:
        """
        Traite les citations pour les réponses Perplexity

        Args:
            response_text: Le texte de la réponse
            response: L'objet réponse de litellm

        Returns:
            Le texte avec les citations formatées
        """
        if self.model_name != "sonar":
            return response_text

        sources = response.citations if hasattr(response, 'citations') and response.citations else []

        if not sources:
            return response_text

        def replace_citation(match):
            citation_num = int(match.group(1))
            if 1 <= citation_num <= len(sources):
                return f" [[{citation_num}]](<{sources[citation_num - 1]}>)"
            return match.group(0)

        processed_text = re.sub(r'\[(\d+)\]', replace_citation, response_text)
        return processed_text

    async def _try_stream_config(self, config: Dict[str, Any], messages: List[Dict[str, Any]],
                               parameters: ChatParameters) -> AsyncGenerator[StreamChunk, None]:
        """Essaie de streamer avec une configuration spécifique"""
        litellm_params = config["litellm_params"]
        tokenizer_name = config.get("tokenizer", self.model_name)

        current_params = {
            "model": litellm_params["model"],
            "api_key": os.getenv(litellm_params["api_key"]),
            "messages": messages,
            "stream": True,
            "temperature": parameters.temperature,
            "drop_params": True
        }

        if parameters.max_tokens:
            current_params["max_tokens"] = parameters.max_tokens

        if "api_base" in litellm_params:
            current_params["api_base"] = litellm_params["api_base"]

        response = litellm.completion(**current_params)

        response_text = ""
        last_chunk = None

        async for chunk in response:
            last_chunk = chunk
            if hasattr(chunk, 'choices') and chunk.choices:
                choice = chunk.choices[0]
                if hasattr(choice, 'delta') and hasattr(choice.delta, 'content'):
                    content = choice.delta.content
                    if content:
                        response_text += content
                        yield StreamChunk(chunk=content, done=False)

        model = last_chunk.model if (last_chunk and hasattr(last_chunk, 'model')) else litellm_params["model"]

        if last_chunk and hasattr(last_chunk, 'usage') and last_chunk.usage:
            usage = last_chunk.usage.total_tokens

        if self.model_name == "sonar" and (not hasattr(last_chunk, 'citations') or not last_chunk.citations):
            non_stream_params = current_params.copy()
            non_stream_params["stream"] = False
            non_stream_response = litellm.completion(**non_stream_params)
            response_text = self._process_perplexity_citations(response_text, non_stream_response)
        else:
            response_text = self._process_perplexity_citations(response_text, last_chunk)

        yield StreamChunk(
            chunk=response_text,
            done=True,
            response=response_text,
            usage=usage,
            model=model,
            elapsed_time=None
        )

    async def _stream_with_fallbacks(self, parameters: ChatParameters,
                                   start_time: datetime) -> AsyncGenerator[StreamChunk, None]:
        """Streaming avec fallbacks personnalisés"""
        configs = self._load_configs()

        with get_client().start_as_current_observation(
            as_type="generation",
            name=f"user-completion-{datetime.now().isoformat()}"
        ) as gen:
            gen.update(input=parameters.messages)

            for config in configs:
                try:
                    async for chunk in self._try_stream_config(config, parameters.messages, parameters):
                        if chunk.done:
                            elapsed_time = self._format_elapsed_time(start_time)

                            gen.update(
                                output=chunk.response,
                                model=chunk.model,
                                usage_details={
                                    "input_tokens": 0,
                                    "output_tokens": chunk.usage,
                                    "total_tokens": chunk.usage
                                },
                                model_parameters={
                                    "temperature": parameters.temperature,
                                    "stream": True
                                }
                            )

                            yield StreamChunk(
                                chunk="",
                                done=True,
                                response=chunk.response,
                                usage=chunk.usage,
                                model=parameters.model,
                                elapsed_time=elapsed_time
                            )
                            return
                        else:
                            yield chunk

                except Exception as e:
                    logger.warning(f"Erreur avec {config['litellm_params']['model']}: {str(e)}")
                    continue

            logger.error("Tous les fallbacks ont échoué")

    async def _non_stream_chat(self, parameters: ChatParameters, start_time: datetime, retry_count: int = 0) -> ChatResult:
        """Chat non-streaming avec fallbacks natifs"""
        configs = self._load_configs()

        # Rotate configs for retry to use different primary model
        if retry_count > 0:
            configs = configs[retry_count:] + configs[:retry_count]

        with get_client().start_as_current_observation(
            as_type="generation",
            name=f"user-completion-{datetime.now().isoformat()}"
        ) as gen:
            gen.update(input=parameters.messages)

            primary_config = configs[0]["litellm_params"]
            fallback_configs = [config["litellm_params"] for config in configs[1:]]

            params = {
                "model": primary_config["model"],
                "api_key": os.getenv(primary_config["api_key"]),
                "messages": parameters.messages,
                "temperature": parameters.temperature,
                "drop_params": True
            }

            if parameters.max_tokens:
                params["max_tokens"] = parameters.max_tokens

            if "api_base" in primary_config:
                params["api_base"] = primary_config["api_base"]

            fallbacks = []
            for fb_config in fallback_configs:
                fb_params = {
                    "model": fb_config["model"],
                    "api_key": os.getenv(fb_config["api_key"])
                }
                if "api_base" in fb_config:
                    fb_params["api_base"] = fb_config["api_base"]
                fallbacks.append(fb_params)

            if fallbacks:
                params["fallbacks"] = fallbacks

            response = litellm.completion(**params)

            usage = response.usage.total_tokens
            model = parameters.model
            response_text = response.choices[0].message.content
            if response_text is None or response_text.strip() == "":
                if retry_count < len(configs) - 1:
                    logger.error("Model returned empty response, retrying ...")
                    return await self._non_stream_chat(parameters, start_time, retry_count + 1)
                else:
                    logger.error("Model returned empty response, all retries exhausted")
                    response_text = "I'm sorry, but I couldn't generate a response. Please try again."
            response_text = self._process_perplexity_citations(response_text, response)

            gen.update(
                output=response_text,
                model=model,
                usage_details={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": usage
                },
                model_parameters={
                    "temperature": parameters.temperature,
                    "stream": False
                }
            )

            return ChatResult(
                response=response_text,
                usage=usage,
                model=model,
                elapsed_time=self._format_elapsed_time(start_time)
            )

    def chat(self, parameters: ChatParameters) -> Union[ChatResult, AsyncGenerator[StreamChunk, None]]:
        """
        Méthode principale pour converser avec le modèle

        Args:
            parameters: Paramètres typés de la conversation

        Returns:
            En mode streaming: AsyncGenerator de StreamChunk
            En mode non-streaming: coroutine that resolves to ChatResult
        """
        start_time = datetime.now()

        if parameters.stream:
            return self._stream_with_fallbacks(parameters, start_time)
        else:
            async def _get_result():
                return await self._non_stream_chat(parameters, start_time, 0)
            return _get_result()

    async def generate(self, parameters: ChatParameters):
        """
        Génère une réponse du modèle

        Args:
            parameters: Paramètres de la conversation

        Yields:
            ChatResult ou StreamChunk selon le mode
        """
        if parameters.stream:
            async for chunk in self.chat(parameters):
                yield chunk
        else:
            result = await self.chat(parameters)
            yield result