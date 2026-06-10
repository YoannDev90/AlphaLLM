"""Create a sandbox and run a command in one step."""

import asyncio
import json
import time
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


async def sandbox_run(
    image: str,
    command: str,
    memoryMib: int = 512,
    cpus: int = 1,
    env: Optional[Dict[str, str]] = None,
) -> str:
    """Create a sandbox, run a command and return the result payload.

    Parameters
    ----------
    image : str
        Container image to use.
    command : str
        Shell command to run.
    memoryMib : int
        Memory limit in MiB (default: 512).
    cpus : int
        Number of CPUs to allocate (default: 1).
    env : Optional[Dict[str, str]]
        Environment overrides (default: None).

    Returns
    -------
    str
        JSON string with the execution result.
    """
    name = f"native-run-{int(time.time() * 1000)}"
    sandbox = None
    try:
        kwargs: Dict[str, Any] = {
            "image": image,
            "memory_mib": memoryMib,
            "cpus": cpus,
        }
        if env:
            kwargs["env"] = env

        try:
            sandbox = await asyncio.to_thread(
                microsandbox.Sandbox.create, name, **kwargs
            )
        except Exception:
            cfg = {
                "name": name,
                "image": image,
                "memoryMib": memoryMib,
                "cpus": cpus,
                "env": env or {},
            }
            sandbox = await asyncio.to_thread(microsandbox.Sandbox.create, cfg)

        output = await asyncio.to_thread(sandbox.shell, command)
        return json.dumps(_extract_exec_result(output), ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_run failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
    finally:
        if sandbox is not None:
            try:
                await asyncio.to_thread(sandbox.stop)
            except Exception:
                pass
            try:
                await asyncio.to_thread(microsandbox.Sandbox.remove, name)
            except Exception:
                pass
