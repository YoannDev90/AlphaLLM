"""Sandbox helper for statting files inside a microsandbox."""

import asyncio
import json
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


async def sandbox_fs_stat(name: str, path: str) -> str:
    """Return stat information for a sandbox path.

    Parameters
    ----------
    name : str
        Sandbox name.
    path : str
        File or directory path to inspect.

    Returns
    -------
    str
        JSON object string describing the file stats.
    """
    try:
        sandbox = await asyncio.to_thread(microsandbox.Sandbox.get, name)
        cmd = (
            "python - <<'PY'\n"
            "import json, os\n"
            f"p = {json.dumps(path)}\n"
            "st = os.stat(p)\n"
            "kind = 'dir' if os.path.isdir(p) else 'file'\n"
            "print(json.dumps({'kind': kind, 'size': st.st_size, 'mode': st.st_mode, 'modified': int(st.st_mtime)}))\n"
            "PY"
        )
        result = await asyncio.to_thread(sandbox.shell, cmd)
        out = _extract_exec_result(result)
        if not out.get("success"):
            return json.dumps(out, ensure_ascii=True, indent=2)
        return str(out.get("stdout") or "{}").strip()
    except Exception as exc:
        logger.error("sandbox_fs_stat failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
