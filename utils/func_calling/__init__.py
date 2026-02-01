"""Function calling helpers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

from utils.func_calling.function_calling import FunctionCaller

_logger = logging.getLogger(__name__)
_function_caller: Optional[FunctionCaller] = None


async def initialize_function_caller() -> FunctionCaller:
    """Initialize the shared function caller."""

    global _function_caller
    if _function_caller is None:
        _logger.debug("Creating shared FunctionCaller instance")
        _function_caller = FunctionCaller()
        await _function_caller.initialize()
        tools_dir = Path("configs/tools")
        tools = []
        if tools_dir.exists():
            for tool_file in tools_dir.glob("*.json"):
                try:
                    with open(tool_file, "r") as f:
                        tool = json.load(f)
                        tools.append(tool)
                except Exception as e:
                    _logger.error(f"Failed to load tool {tool_file}: {e}")
        _function_caller.set_tools(tools)
        _logger.info(f"Shared FunctionCaller ready with {len(tools)} tools")
    return _function_caller


async def get_function_caller() -> FunctionCaller:
    """Return the shared FunctionCaller, initializing it if needed."""

    if _function_caller is None:
        await initialize_function_caller()
    assert _function_caller is not None
    return _function_caller


__all__ = [
    "FunctionCaller",
    "initialize_function_caller",
    "get_function_caller",
]
