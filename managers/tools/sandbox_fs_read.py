"""Sandbox helper for reading files inside a microsandbox."""

import asyncio
import json
import shlex
from typing import Any, Dict

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


async def sandbox_fs_read(name: str, path: str) -> str:
    """Read a file from inside a sandbox.

    Parameters
    ----------
    name : str
        Sandbox name.
    path : str
        File path to read.

    Returns
    -------
    str
        File contents or a JSON error payload.
    """
    try:
        sandbox = await asyncio.to_thread(microsandbox.Sandbox.get, name)
        cmd = f"cat {shlex.quote(path)}"
        result = await asyncio.to_thread(sandbox.shell, cmd)
        out = _extract_exec_result(result)
        if out.get("success"):
            return str(out.get("stdout") or "")
        return json.dumps(out, ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_fs_read failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
