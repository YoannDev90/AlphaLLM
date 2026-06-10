"""Execute commands inside an existing microsandbox."""

import asyncio
import json
from typing import Any, Dict, List, Optional

import microsandbox

from utils.logger import get_logger

logger = get_logger()


def _extract_exec_result(result: Any) -> Dict[str, Any]:
    """Normalize a sandbox execution result into a JSON-friendly dict.

    Parameters
    ----------
    result : Any
        Raw execution result returned by microsandbox.

    Returns
    -------
    Dict[str, Any]
        Dictionary with stdout, stderr, exit code and success.
    """
    stdout = getattr(result, "stdout", None)
    stderr = getattr(result, "stderr", None)
    code = getattr(result, "code", None)
    success = getattr(result, "success", None)

    if callable(stdout):
        stdout = stdout()
    if callable(stderr):
        stderr = stderr()
    if callable(success):
        success = success()

    return {
        "stdout": stdout,
        "stderr": stderr,
        "exitCode": code,
        "success": success,
    }


async def sandbox_exec(
    name: str,
    command: str,
    args: Optional[List[str]] = None,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
) -> str:
    """Execute a command in an existing sandbox.

    Parameters
    ----------
    name : str
        Sandbox name.
    command : str
        Executable or command to run.
    args : Optional[List[str]]
        Optional argument list (default: None).
    cwd : Optional[str]
        Optional working directory (default: None).
    env : Optional[Dict[str, str]]
        Optional environment overrides (default: None).
    timeout : Optional[float]
        Optional timeout in seconds (default: None).

    Returns
    -------
    str
        JSON string with the normalized execution result.
    """
    try:
        sandbox = await asyncio.to_thread(microsandbox.Sandbox.get, name)

        options: Dict[str, Any] = {}
        if args:
            options["args"] = args
        if cwd:
            options["cwd"] = cwd
        if env:
            options["env"] = env
        if timeout is not None:
            options["timeout"] = int(timeout * 1000)

        if options:
            result = await asyncio.to_thread(sandbox.exec, command, options)
        elif args:
            result = await asyncio.to_thread(sandbox.exec, command, args)
        else:
            result = await asyncio.to_thread(sandbox.exec, command)

        return json.dumps(_extract_exec_result(result), ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_exec failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
