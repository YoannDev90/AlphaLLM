"""Function calling implementation using Native SDKs (Groq, Cerebras)."""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from groq import AsyncGroq
from cerebras.cloud.sdk import AsyncCerebras

from config import LOGGER_NAME, read_file

logger = logging.getLogger(LOGGER_NAME)


class FunctionCaller:
    """Function calling wrapper using Native SDKs instead of LiteLLM."""

    def __init__(self, config_path: str = "configs/misc/tool_calling.json") -> None:
        self._logger = logging.getLogger(LOGGER_NAME)
        self.config_path = config_path
        self._configs: List[Dict[str, Any]] = []
        self._tools: List[Dict[str, Any]] = []
        self._load_configs()

    def _load_configs(self) -> None:
        """Load configurations for tool calling."""
        try:
            with open(self.config_path, "r") as f:
                self._configs = json.load(f)
        except Exception as e:
            self._logger.error(f"Failed to load tool calling config: {e}")
            self._configs = []

    async def initialize(self) -> None:
        """Initialization for compatibility."""
        pass

    def set_tools(self, tools: List[Dict[str, Any]]) -> None:
        """Set the available tools."""
        self._tools = tools

    async def check_for_tools(self, user_content: str) -> List[Dict[str, Any]]:
        """Check if the input requires tool calling using native SDKs (Groq/Cerebras)."""
        if not self._tools or not self._configs:
            return []

        messages = [
            {
                "role": "system",
                "content": read_file("configs/prompts/function_calling.txt"),
            },
            {"role": "user", "content": user_content},
        ]

        # OpenAI compatible tools format
        formatted_tools = []
        for tool in self._tools:
            if isinstance(tool, dict) and tool.get("type") == "function":
                formatted_tools.append(tool)
            else:
                formatted_tools.append({"type": "function", "function": tool})

        for config in self._configs:
            try:
                litellm_params = config.get("litellm_params", {}).copy()
                model = litellm_params.get("model", "")
                api_key_env = litellm_params.get("api_key")
                api_key = os.environ.get(api_key_env) if api_key_env else None

                if not api_key:
                    self._logger.error(f"API Key {api_key_env} not found for model {model}")
                    continue

                tool_calls = []
                
                if "groq" in model:
                    client = AsyncGroq(api_key=api_key)
                    clean_model = model.split("/")[-1]
                    response = await client.chat.completions.create(
                        model=clean_model,
                        messages=messages,
                        tools=formatted_tools,
                        tool_choice="auto",
                    )
                    message = response.choices[0].message
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tool_call in message.tool_calls:
                            try:
                                func_name = tool_call.function.name
                                params = json.loads(tool_call.function.arguments)
                                tool_calls.append({"function": func_name, "parameters": params})
                            except Exception as e:
                                self._logger.warning(f"Failed to parse Groq tool call: {e}")

                elif "cerebras" in model:
                    client = AsyncCerebras(api_key=api_key)
                    clean_model = model.split("/")[-1]
                    response = await client.chat.completions.create(
                        model=clean_model,
                        messages=messages,
                        tools=formatted_tools,
                        tool_choice="auto",
                    )
                    message = response.choices[0].message
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tool_call in message.tool_calls:
                            try:
                                func_name = tool_call.function.name
                                params = json.loads(tool_call.function.arguments)
                                tool_calls.append({"function": func_name, "parameters": params})
                            except Exception as e:
                                self._logger.warning(f"Failed to parse Cerebras tool call: {e}")

                if tool_calls:
                    return tool_calls

            except Exception as e:
                # Capture de la génération échouée de Groq (Llama 3.1 specific error)
                error_msg = str(e)
                if "failed_generation" in error_msg:
                    try:
                        # Recherche du pattern <function=name>{args}
                        pattern = r"<function=(?P<name>[^>]+)>(?P<args>.*?)(?:</function>|$)"
                        match = re.search(pattern, error_msg, re.DOTALL)
                        if match:
                            func_name = match.group("name")
                            args_raw = match.group("args").strip()
                            
                            # Nettoyage JSON agressif pour Llama (clés sans guillemets, etc.)
                            args_fixed = re.sub(r'([{,])\s*([a-zA-Z_]\w*)\s*:', r'\1"\2":', args_raw)
                            # Correction spécifique pour "Category ID" (espace bloquant)
                            args_fixed = args_fixed.replace('"Category ID"', '"category_id"')
                            
                            params = json.loads(args_fixed)
                            self._logger.info(f"Fallback parsing success: {func_name}")
                            return [{"function": func_name, "parameters": params}]
                    except Exception as parse_err:
                        self._logger.warning(f"Failed to parse failed_generation fallback: {parse_err}")

                self._logger.error(f"Tool calling with {config.get('model_name')} using native SDK failed: {e}")
                continue

        return []
