"""Function calling implementation using transformers."""

import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from transformers import AutoModelForCausalLM, AutoProcessor

from config import (FUNCTION_CALLING_CACHE_DIR, FUNCTION_CALLING_MODEL,
                    LOGGER_NAME)

logger = logging.getLogger(LOGGER_NAME)
CACHE_DIR = Path(FUNCTION_CALLING_CACHE_DIR)


class FunctionCaller:
    """Function calling model wrapper."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self._logger = logging.getLogger(LOGGER_NAME)
        self.model_name = model_name or FUNCTION_CALLING_MODEL
        self._processor: Optional[AutoProcessor] = None
        self._model: Optional[AutoModelForCausalLM] = None
        self._tools: List[Dict[str, Any]] = []
        # Defer initialization to async method

    async def initialize(self) -> None:
        """Async initialize processor and model."""
        if self._processor is not None and self._model is not None:
            return
        os.makedirs(CACHE_DIR, exist_ok=True)
        load_start = time.time()
        self._processor = await asyncio.to_thread(
            AutoProcessor.from_pretrained,
            self.model_name,
            cache_dir=str(CACHE_DIR),
            device_map="auto",
        )
        self._model = await asyncio.to_thread(
            AutoModelForCausalLM.from_pretrained,
            self.model_name,
            cache_dir=str(CACHE_DIR),
            dtype="auto",
            device_map="auto",
        )
        load_time = time.time() - load_start
        self._logger.info(
            f"Function calling model {self.model_name} loaded in {load_time:.4f}s"
        )

    def set_tools(self, tools: List[Dict[str, Any]]) -> None:
        """Set the available tools."""
        self._tools = tools

    def parse_function_calls(self, output: str) -> List[Dict[str, Any]]:
        """Parse function calls from model output."""
        calls = []
        pattern = r"<start_function_call>(.*?)<end_function_call>"
        matches = re.findall(pattern, output, re.DOTALL)
        for match in matches:
            if match.startswith("call:"):
                func_part = match[5:]
                brace_start = func_part.find("{")
                if brace_start != -1:
                    func_name = func_part[:brace_start]
                    params_str = func_part[brace_start:]
                    params_str = params_str.replace("<escape>", "").replace(
                        "</escape>", ""
                    )
                    try:
                        params = {}
                        if params_str.startswith("{") and params_str.endswith("}"):
                            inner = params_str[1:-1]
                            pairs = [p.strip() for p in inner.split(",")]
                            for pair in pairs:
                                if ":" in pair:
                                    key, value = pair.split(":", 1)
                                    params[key.strip()] = value.strip().strip('"')
                        calls.append({"function": func_name, "parameters": params})
                    except Exception as e:
                        self._logger.warning(f"Failed to parse function call: {e}")
        return calls

    def generate_response(self, user_content: str) -> str:
        """Generate response from the function calling model."""
        start_time = time.time()
        message = [
            {
                "role": "developer",
                "content": "You are a model that can do function calling with the following functions",
            },
            {"role": "user", "content": user_content},
        ]
        template_start = time.time()
        inputs = self._processor.apply_chat_template(
            message,
            tools=self._tools,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        template_time = time.time() - template_start

        generate_start = time.time()
        out = self._model.generate(
            **inputs.to(self._model.device),
            pad_token_id=self._processor.eos_token_id,
            max_new_tokens=256,
        )
        generate_time = time.time() - generate_start

        decode_start = time.time()
        output = self._processor.decode(
            out[0][len(inputs["input_ids"][0]) :], skip_special_tokens=True
        )
        decode_time = time.time() - decode_start

        total_time = time.time() - start_time
        self._logger.debug(
            f"Function calling - Template: {template_time:.4f}s, Generate: {generate_time:.4f}s, "
            f"Decode: {decode_time:.4f}s, Total: {total_time:.4f}s"
        )
        return output

    def check_for_tools(self, user_content: str) -> List[Dict[str, Any]]:
        """Check if the input requires tool calling."""
        if not self._tools:
            return []
        output = self.generate_response(user_content)
        return self.parse_function_calls(output)
