"""MCP (Model-Context-Protocol) manager for external tool servers.

Handles loading MCP server configurations, initializing `fastmcp` clients,
and exposing remote tools as local function metadata.
"""

import asyncio
import json
import os
import shlex
import subprocess
import traceback
from typing import Any, Dict, List

from fastmcp import Client

from core.config import cfg
from utils.logger import get_logger

logger = get_logger()


class MCPManager:
    """Manager for MCP servers and their exposed tools.

    The manager loads configuration from disk, initializes `fastmcp.Client`
    instances for each configured server and collects metadata about
    available tools to expose them to the rest of the application.
    """

    def __init__(self, config_path: str):
        """Create an MCPManager.

        Parameters
        ----------
        config_path : str
            Path to the JSON file containing MCP server configurations.
        """
        self.config_path = config_path
        self.clients: Dict[str, Client] = {}
        self.client_configs: Dict[str, Dict[str, Any]] = {}
        self.server_raw_configs: Dict[str, Dict[str, Any]] = {}
        self.tools_metadata: List[Dict[str, Any]] = []

    def _debug_run_command(
        self, command: str, args: List[str], env: Dict[str, str]
    ) -> Dict[str, str]:
        """Run a command locally and capture stdout/stderr for debugging.

        Parameters
        ----------
        command : str
            Executable to run.
        args : List[str]
            Additional arguments for the command.
        env : Dict[str, str]
            Environment variables to use for the subprocess.

        Returns
        -------
        Dict[str, str]
            Dictionary containing returncode, stdout, stderr and cmdline.
        """
        cmd = [command] + (args or [])
        try:
            proc = subprocess.run(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
            )
            return {
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "cmdline": " ".join(shlex.quote(x) for x in cmd),
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "cmdline": " ".join(shlex.quote(x) for x in cmd),
            }

    def _prepare_runtime_env(self, base_env: Dict[str, str]) -> Dict[str, str]:
        """Prepare a runtime environment for launching MCP subprocesses.

        Ensures `~/.microsandbox/bin` is on `PATH` and sets `MSB_PATH` when
        the microsandbox binary is available.

        Parameters
        ----------
        base_env : Dict[str, str]
            Base environment to copy and extend.

        Returns
        -------
        Dict[str, str]
            Modified environment dictionary.
        """
        env = base_env.copy()
        msb_path = os.path.expanduser("~/.microsandbox/bin")
        msb_binary = os.path.join(msb_path, "msb")

        if msb_path not in env.get("PATH", ""):
            env["PATH"] = f"{msb_path}:{env.get('PATH', '')}"

        if os.path.exists(msb_binary):
            env.setdefault("MSB_PATH", msb_binary)

        return env

    def load_config(self):
        """Load MCP configuration JSON from disk.

        Returns
        -------
        dict
            Parsed JSON object or empty dict if file missing.
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"MCP config not found at {self.config_path}")
            return {}
        with open(self.config_path, "r") as f:
            return json.load(f)

    async def initialize(self):
        """Initialize all configured MCP servers.

        Loads configuration and initializes clients for each server
        (via `_initialize_server`).
        """
        config = self.load_config()
        servers = config.get("mcpServers", {})

        tasks = []
        for name, srv_config in servers.items():
            tasks.append(self._initialize_server(name, srv_config))

        if tasks:
            await asyncio.gather(*tasks)

    async def _initialize_server(self, name: str, srv_config: Dict[str, Any]):
        """Initialize a single MCP server and collect its tools.

        Parameters
        ----------
        name : str
            Server logical name from configuration.
        srv_config : Dict[str, Any]
            Server configuration dictionary.
        """
        try:
            logger.debug(f"Initializing MCP server: {name}")

            # persist raw server config for later debug
            self.server_raw_configs[name] = srv_config

            # Check for SSE URL (for search.parallel.ai/mcp)
            if "url" in srv_config:
                client_config = {
                    "mcpServers": {
                        name: {
                            "url": srv_config["url"],
                            "headers": srv_config.get("headers", {}),
                        }
                    }
                }
            else:
                # Stdio config
                env = self._prepare_runtime_env(os.environ.copy())

                srv_env = srv_config.get("env", {})
                env.update(srv_env)

                client_config = {
                    "mcpServers": {
                        name: {
                            "command": srv_config["command"],
                            "args": srv_config.get("args", []),
                            "env": env,
                        }
                    }
                }

            # keep client_config copy for debugging
            self.client_configs[name] = client_config
            try:
                logger.debug(
                    f"MCP client_config for {name}: {json.dumps({k: (v if k != 'env' else list(v.keys())) for k, v in client_config['mcpServers'][name].items()}, default=str)}"
                )
            except Exception:
                logger.debug(
                    f"MCP client_config for {name}: (unserializable) {repr(client_config)}"
                )

            client = Client(client_config)
            self.clients[name] = client

            # Connection must be established via context manager to allow list_tools()
            async with client:
                tools = await client.list_tools()
                logger.debug(f"Raw tools for {name}: {repr(tools)[:2000]}")
                for tool in tools:
                    # Map to OpenAI/LiteLLM function format
                    # In fastmcp Client, tool parameters are in inputSchema or input_schema
                    params = getattr(
                        tool, "inputSchema", getattr(tool, "parameters", {})
                    )
                    if hasattr(params, "model_dump"):
                        params = params.model_dump()

                    self.tools_metadata.append(
                        {
                            "type": "function",
                            "function": {
                                "name": f"mcp_{name}_{tool.name}",
                                "description": tool.description,
                                "parameters": params,
                            },
                        }
                    )
                logger.debug(f"Loaded {len(tools)} tools from {name}")
                try:
                    fnames = [f"mcp_{name}_{t.name}" for t in tools]
                    logger.debug(f"Exposed functions from {name}: {fnames}")
                except Exception:
                    logger.debug("Failed to list exposed function names")
        except Exception as e:
            logger.error(f"Failed to initialize MCP server {name}: {e}")
            logger.error(traceback.format_exc())
            # If server configured with command, try local dry-run to see immediate stderr/stdout
            try:
                srv = self.server_raw_configs.get(name, {})
                if srv and "command" in srv:
                    env = self._prepare_runtime_env(os.environ.copy())
                    env.update(srv.get("env", {}))
                    run = self._debug_run_command(
                        srv["command"], srv.get("args", []), env
                    )
                    logger.error(
                        f"Local command debug for {name}: cmd={run.get('cmdline')} rc={run.get('returncode')} stdout={run.get('stdout')[:2000]} stderr={run.get('stderr')[:2000]}"
                    )
            except Exception:
                logger.error("Failed to run local command debug")
                logger.error(traceback.format_exc())

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> str:
        """Call a tool on a remote MCP server and return its result.

        Parameters
        ----------
        server_name : str
            Logical name of the configured MCP server.
        tool_name : str
            Name of the tool to invoke on the remote server.
        arguments : Dict[str, Any]
            Arguments to pass to the tool.

        Returns
        -------
        str
            Stringified result or an error message on failure.
        """
        client = self.clients.get(server_name)
        if not client:
            logger.error(f"MCP tool call failed: Server '{server_name}' not found")
            return f"Error: MCP server {server_name} not found."

        logger.info(
            f"Calling MCP tool: {server_name}.{tool_name} with args: {arguments}"
        )
        try:
            # call_tool in fastmcp requires an active connection
            async with client:
                logger.info(
                    f"Connected to MCP server {server_name} for tool call {tool_name}"
                )
                try:
                    result = await client.call_tool(tool_name, arguments, timeout=60)
                    logger.info(
                        f"MCP tool {server_name}.{tool_name} returned: {str(result)[:500]}..."
                    )
                    # If result exposes stdout/stderr, log snippets
                    try:
                        stdout = getattr(result, "stdout", None)
                        stderr = getattr(result, "stderr", None)
                        if stdout:
                            logger.debug(f"Tool stdout (trunc): {str(stdout)[:2000]}")
                        if stderr:
                            logger.debug(f"Tool stderr (trunc): {str(stderr)[:2000]}")
                    except Exception:
                        logger.debug("Failed to introspect tool result")
                    return str(result)
                except Exception as inner:
                    logger.error(
                        f"Inner error calling tool {tool_name} on {server_name}: {inner}"
                    )
                    logger.error(traceback.format_exc())
                    # If server has local command config, run local dry-run to capture startup failure
                    try:
                        srv = self.server_raw_configs.get(server_name, {})
                        if srv and "command" in srv:
                            env = self._prepare_runtime_env(os.environ.copy())
                            env.update(srv.get("env", {}))
                            run = self._debug_run_command(
                                srv["command"], srv.get("args", []), env
                            )
                            logger.error(
                                f"Local command debug for {server_name}: cmd={run.get('cmdline')} rc={run.get('returncode')} stdout={run.get('stdout')[:2000]} stderr={run.get('stderr')[:2000]}"
                            )
                    except Exception:
                        logger.error("Failed to run local command debug in call_tool")
                        logger.error(traceback.format_exc())
                    return f"Error: {str(inner)}"
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name} on {server_name}: {e}")
            logger.error(traceback.format_exc())
            return f"Error: {str(e)}"


# Singleton instance
MCP_CONFIG_PATH = os.path.join(cfg.BASE_DIR, "config", "mcp.json")
mcp_manager = MCPManager(MCP_CONFIG_PATH)
