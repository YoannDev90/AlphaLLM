"""Tool registry helpers for combining native and MCP tools."""

import json
import os

from managers.mcp import mcp_manager
from managers.tools import ToolsLoader
from utils.logger import get_logger

logger = get_logger()

# Initialize tools loader
TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "tools")
tools_loader = ToolsLoader(TOOLS_DIR)

# Log summary of loaded native tools
try:
    native_names = []
    for t in tools_loader.tools_metadata:
        if isinstance(t, dict) and t.get("type") == "function":
            fn = t.get("function", {})
            native_names.append(fn.get("name") or fn.get("description") or "<unnamed>")
        else:
            try:
                native_names.append(t.get("name") if isinstance(t, dict) else str(t))
            except Exception:
                native_names.append(str(t))

    logger.debug("Native tools: %d found", len(native_names))
    logger.debug("Native tool names: %s", native_names)
except Exception:
    logger.debug("Failed to summarize native tools")


def get_combined_tools():
    """Returns combined tools from native tools + MCP tools.

    Returns
    -------
    list
        Combined list of tool descriptors.
    """
    return tools_loader.tools_metadata + mcp_manager.tools_metadata


async def handle_tool_call(tool_name: str, args: dict) -> str:
    """Execute requested tool. Routes to native tools or MCP tools.

    Parameters
    ----------
    tool_name : str
        Tool name to execute.
    args : dict
        Arguments forwarded to the tool.

    Returns
    -------
    str
        Tool result string or error message.
    """
    try:
        # Check if it's a native tool
        if tool_name in tools_loader.tools_handlers:
            return await tools_loader.call_tool(tool_name, args)

        # Check if it's an MCP tool (format: mcp_SERVERNAME_TOOLNAME)
        if tool_name.startswith("mcp_"):
            parts = tool_name.split("_", 2)
            if len(parts) >= 3:
                server_name = parts[1]
                actual_tool_name = parts[2]
                return await mcp_manager.call_tool(server_name, actual_tool_name, args)

        return "Unknown tool."

    except Exception as e:
        logger.error(f"Error in tool {tool_name}: {e}")
        return f"Error during tool {tool_name} execution: {str(e)}"
