"""Function calling implementation using LiteLLM."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import litellm

from config import LOGGER_NAME, read_file

logger = logging.getLogger(LOGGER_NAME)


class FunctionCaller:
    """Function calling wrapper using LiteLLM."""

    def __init__(self, config_path: str = "configs/misc/tool_calling.json") -> None:
        self._logger = logging.getLogger(LOGGER_NAME)
        self.config_path = config_path
        self._configs: List[Dict[str, Any]] = []
        self._tools: List[Dict[str, Any]] = []
        self._load_configs()

    def _load_configs(self) -> None:
        """Load LiteLLM configurations for tool calling."""
        try:
            with open(self.config_path, "r") as f:
                self._configs = json.load(f)
        except Exception as e:
            self._logger.error(f"Failed to load tool calling config: {e}")
            self._configs = []

    async def initialize(self) -> None:
        """Initialization for compatibility - no complex model loading needed."""
        pass

    def set_tools(self, tools: List[Dict[str, Any]]) -> None:
        """Set the available tools."""
        self._tools = tools

    async def check_for_tools(self, user_content: str) -> List[Dict[str, Any]]:
        """Check if the input requires tool calling using LiteLLM."""
        if not self._tools or not self._configs:
            return []

        messages = [
            {
                "role": "system",
                "content": read_file("configs/prompts/function_calling.txt"),
            },
            {"role": "user", "content": user_content},
        ]

        # LiteLLM tools format (OpenAI compatible)
        formatted_tools = []
        for tool in self._tools:
            formatted_tools.append({"type": "function", "function": tool})

        for config in self._configs:
            try:
                litellm_params = config.get("litellm_params", {}).copy()
                model = litellm_params.pop("model")
                api_key_env = litellm_params.pop("api_key", None)
                api_key = os.environ.get(api_key_env) if api_key_env else None

                response = await litellm.acompletion(
                    model=model,
                    messages=messages,
                    tools=formatted_tools,
                    tool_choice="auto",
                    api_key=api_key,
                    **litellm_params,
                )

                message = response.choices[0].message
                if hasattr(message, "tool_calls") and message.tool_calls:
                    calls = []
                    for tool_call in message.tool_calls:
                        try:
                            func_name = tool_call.function.name
                            params = json.loads(tool_call.function.arguments)
                            calls.append({"function": func_name, "parameters": params})
                        except Exception as e:
                            self._logger.warning(f"Failed to parse tool call arguments: {e}")
                    return calls
                
                return []

            except Exception as e:
                self._logger.error(f"Tool calling with {config.get('model_name')} failed: {e}")
                continue

        return []
