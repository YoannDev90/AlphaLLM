"""Function calling implementation using Native SDKs with dynamic dispatch."""

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
    """Dynamic function calling wrapper using Native SDKs."""

    def __init__(self, config_path: str = "configs/misc/tool_calling.json") -> None:
        self._logger = logging.getLogger(LOGGER_NAME)
        self.config_path = config_path
        self._configs: List[Dict[str, Any]] = []
        self._tools: List[Dict[str, Any]] = []
        self._load_configs()
        
        # Clients cache and rotation index
        self._clients = {}
        self._current_config_idx = 0

    def _load_configs(self) -> None:
        """Load provider configurations."""
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

    def _get_client(self, provider: str, api_key: str):
        """Get or create a cached client for the provider."""
        if provider not in self._clients:
            if provider == "groq":
                self._clients[provider] = AsyncGroq(api_key=api_key)
            elif provider == "cerebras":
                self._clients[provider] = AsyncCerebras(api_key=api_key)
        return self._clients.get(provider)

    async def _call_native_sdk(self, config: Dict[str, Any], messages: List[Dict], tools: List[Dict]) -> List[Dict]:
        """Generic native SDK call based on provider in model string."""
        litellm_params = config.get("litellm_params", {})
        full_model = litellm_params.get("model", "")
        api_key_env = litellm_params.get("api_key")
        api_key = os.environ.get(api_key_env) if api_key_env else None

        if not api_key:
            return []

        # Determine provider (e.g., "groq/llama..." -> "groq")
        provider = "groq" if "groq" in full_model else "cerebras" if "cerebras" in full_model else None
        if not provider:
            return []

        clean_model = full_model.split("/")[-1]
        client = self._get_client(provider, api_key)
        
        try:
            response = await client.chat.completions.create(
                model=clean_model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            msg = response.choices[0].message
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                return [{"function": t.function.name, "parameters": json.loads(t.function.arguments)} for t in msg.tool_calls]
            return []

        except Exception as e:
            # Smart Fallback for malformed formats (specific to Llama/Groq)
            error_msg = str(e)
            if "failed_generation" in error_msg:
                return self._parse_malformed_generation(error_msg)
            raise e

    def _parse_malformed_generation(self, error_msg: str) -> List[Dict]:
        """Ultra-resilient parser for malformed function calls."""
        try:
            pattern = r"<function=(?P<name>[^>]+)>(?P<args>.*?)(?:</function>|$)"
            match = re.search(pattern, error_msg, re.DOTALL)
            if not match: return []

            func_name = match.group("name")
            args_raw = match.group("args").strip()

            # 1. Clean missing quotes on keys
            args_fixed = re.sub(r'([{,])\s*([a-zA-Z_][\w\s]*?)\s*:', r'\1"\2":', args_raw)
            # 2. Fix common key naming errors
            args_fixed = args_fixed.replace('"Category ID"', '"category_id"').replace('"User ID"', '"user_id"')
            # 3. Fix unescaped single quotes in French/English text values
            args_fixed = re.sub(r':\s*"([^"]*?)"', lambda m: ': "' + m.group(1).replace('"', '\\"') + '"', args_fixed)

            try:
                return [{"function": func_name, "parameters": json.loads(args_fixed)}]
            except:
                # Last resort: Regex extraction of parameters
                params = {}
                # Extract all "key": "value" pairs even in broken JSON
                pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', args_fixed)
                for k, v in pairs:
                    # Map common naming mistakes back to schema keys
                    k_clean = k.lower().replace(" ", "_")
                    params[k_clean] = v
                return [{"function": func_name, "parameters": params}] if params else []
        except:
            return []

    async def check_for_tools(self, user_content: str) -> List[Dict[str, Any]]:
        """Main entry point with provider rotation (round-robin)."""
        if not self._tools or not self._configs:
            return []

        messages = [
            {"role": "system", "content": read_file("configs/prompts/function_calling.txt")},
            {"role": "user", "content": user_content},
        ]

        formatted_tools = [
            (t if (isinstance(t, dict) and t.get("type") == "function") else {"type": "function", "function": t})
            for t in self._tools
        ]

        # Rotate starting index to alternate between providers
        num_configs = len(self._configs)
        for i in range(num_configs):
            attempt_idx = (self._current_config_idx + i) % num_configs
            config = self._configs[attempt_idx]
            
            try:
                calls = await self._call_native_sdk(config, messages, formatted_tools)
                if calls:
                    # Update index for NEXT call to start with the other provider
                    self._current_config_idx = (attempt_idx + 1) % num_configs
                    return calls
            except Exception as e:
                self._logger.error(f"Provider {config.get('model_name')} failed: {e}")
                continue
        
        # Increment index even if no tools found to keep alternating
        self._current_config_idx = (self._current_config_idx + 1) % num_configs
        return []
