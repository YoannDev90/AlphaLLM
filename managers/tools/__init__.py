"""Tool loading helpers for `managers.tools`.

This package loads tool metadata from JSON files and resolves the matching
Python handler functions used by the bot and sandbox integration.
"""

import json
import os
import time
from typing import Any, Dict, List

from utils.logger import get_logger

logger = get_logger()


class ToolsLoader:
    """Load tool metadata and handler callables from a tools directory.

    Attributes
    ----------
    tools_dir : str
        Directory containing JSON tool definitions.
    tools_metadata : List[Dict[str, Any]]
        Normalized metadata entries for loaded tools.
    tools_handlers : Dict[str, Any]
        Mapping of tool names to async handler callables.
    """

    def __init__(self, tools_dir: str):
        """Create a loader for the given tools directory.

        Parameters
        ----------
        tools_dir : str
            Path to the directory containing tool JSON files.
        """
        self.tools_dir = tools_dir
        self.tools_metadata: List[Dict[str, Any]] = []
        self.tools_handlers: Dict[str, Any] = {}
        self._load_tools()

    def _load_tools(self):
        """Load all tool definitions from JSON files."""
        start = time.perf_counter()
        loaded = []
        failed = []
        if not os.path.exists(self.tools_dir):
            logger.warning(f"Tools directory not found: {self.tools_dir}")
            return

        for filename in os.listdir(self.tools_dir):
            if not filename.endswith(".json"):
                continue

            tool_name = filename[:-5]  # Remove .json
            json_path = os.path.join(self.tools_dir, filename)

            try:
                with open(json_path, "r") as f:
                    raw = json.load(f)

                # Normalize metadata to function schema expected by LLM clients
                try:
                    name_field = (
                        raw.get("name", tool_name)
                        if isinstance(raw, dict)
                        else tool_name
                    )
                    description = (
                        raw.get("description", "") if isinstance(raw, dict) else ""
                    )
                    parameters = raw.get("inputSchema") or raw.get("parameters") or {}
                    metadata = {
                        "type": "function",
                        "function": {
                            "name": name_field,
                            "description": description,
                            "parameters": parameters,
                        },
                    }
                except Exception:
                    metadata = raw

                self.tools_metadata.append(metadata)

                # Dynamically import handler
                try:
                    module = __import__(
                        f"managers.tools.{tool_name}", fromlist=[tool_name]
                    )
                    handler = getattr(module, tool_name)
                    self.tools_handlers[tool_name] = handler
                    loaded.append(tool_name)
                    logger.debug("Loaded tool: %s", tool_name)
                except ImportError as e:
                    failed.append(tool_name)
                    logger.error(
                        "Failed to import handler for %s: %s",
                        tool_name,
                        e,
                        exc_info=True,
                    )

            except Exception as e:
                failed.append(tool_name)
                logger.error("Failed to load tool %s: %s", tool_name, e, exc_info=True)

        elapsed = time.perf_counter() - start
        logger.info(
            "ToolsLoader: loaded %d tools, failed %d, in %.2fs",
            len(loaded),
            len(failed),
            elapsed,
        )
        if loaded:
            logger.debug("Tools loaded: %s", ", ".join(loaded))
        if failed:
            logger.debug("Tools failed: %s", ", ".join(failed))

    async def call_tool(self, tool_name: str, args: dict) -> str:
        """Call a loaded tool handler and return its result.

        Parameters
        ----------
        tool_name : str
            Name of the loaded tool to invoke.
        args : dict
            Keyword arguments forwarded to the tool handler.

        Returns
        -------
        str
            Result returned by the tool handler, or an error string.
        """
        if tool_name not in self.tools_handlers:
            return f"Unknown tool: {tool_name}"

        try:
            handler = self.tools_handlers[tool_name]
            result = await handler(**args)
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return f"Error: {str(e)}"
