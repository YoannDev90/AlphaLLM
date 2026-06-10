"""Sandbox helper for creating directories inside a microsandbox."""

import asyncio
import json
import shlex
from typing import Any, Dict

import microsandbox

from utils.logger import get_logger

logger = get_logger()


def _extract_exec_result(result: Any) -> Dict[str, Any]:
    """Extract a normalized result payload from a sandbox execution result.

    Parameters
    ----------
    result : Any
        Raw execution result returned by microsandbox.

    Returns
    -------
    Dict[str, Any]
        Normalized dictionary with stdout, stderr, exit code and success.
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


async def sandbox_fs_mkdir(name: str, path: str) -> str:
    """Create a directory inside a sandbox.

    Parameters
    ----------
    name : str
        Sandbox name.
    path : str
        Directory path to create.

    Returns
    -------
    str
        JSON payload describing the mkdir result.
    """
    try:
        sandbox = await asyncio.to_thread(microsandbox.Sandbox.get, name)
        cmd = f"mkdir -p {shlex.quote(path)}"
        result = await asyncio.to_thread(sandbox.shell, cmd)
        out = _extract_exec_result(result)
        if not out.get("success"):
            return json.dumps(out, ensure_ascii=True, indent=2)
        return json.dumps({"path": path, "created": True}, ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_fs_mkdir failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
