"""Sandbox helper for writing files inside a microsandbox."""

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


async def sandbox_fs_write(name: str, path: str, content: str) -> str:
    """Write text content to a file inside a sandbox.

    Parameters
    ----------
    name : str
        Sandbox name.
    path : str
        Destination path inside the sandbox.
    content : str
        Text content to write.

    Returns
    -------
    str
        JSON payload describing the write result.
    """
    try:
        sandbox = await asyncio.to_thread(microsandbox.Sandbox.get, name)
        encoded = json.dumps(content)
        cmd = (
            f"mkdir -p $(dirname {shlex.quote(path)}) && "
            "python - <<'PY'\n"
            "from pathlib import Path\n"
            f"p = Path({json.dumps(path)})\n"
            "p.parent.mkdir(parents=True, exist_ok=True)\n"
            f"p.write_text({encoded}, encoding='utf-8')\n"
            "print('ok')\n"
            "PY"
        )
        result = await asyncio.to_thread(sandbox.shell, cmd)
        out = _extract_exec_result(result)
        if not out.get("success"):
            return json.dumps(out, ensure_ascii=True, indent=2)
        return json.dumps({"path": path, "written": True}, ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_fs_write failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
