"""Execute shell commands inside a microsandbox."""

import asyncio
import json
from typing import Any, Dict, Optional

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


async def sandbox_shell(
    name: str, command: str, timeout: Optional[float] = None
) -> str:
    """Execute a shell command in an existing sandbox.

    Parameters
    ----------
    name : str
        Sandbox name.
    command : str
        Shell command to execute.
    timeout : Optional[float]
        Optional timeout in seconds (default: None).

    Returns
    -------
    str
        JSON string with the normalized execution result.
    """
    try:
        sandbox = await asyncio.to_thread(microsandbox.Sandbox.get, name)
        if timeout is not None:
            result = await asyncio.to_thread(
                sandbox.exec,
                "sh",
                {"args": ["-c", command], "timeout": int(timeout * 1000)},
            )
        else:
            result = await asyncio.to_thread(sandbox.shell, command)
        return json.dumps(_extract_exec_result(result), ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_shell failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
