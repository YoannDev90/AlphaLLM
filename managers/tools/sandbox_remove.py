"""Remove microsandbox instances from the runtime."""

import asyncio
import json

import microsandbox

from utils.logger import get_logger

logger = get_logger()


async def sandbox_remove(name: str, force: bool = False) -> str:
    """Remove a sandbox by name, optionally killing it first.

    Parameters
    ----------
    name : str
        Sandbox name.
    force : bool
        If True, kill the sandbox before removing it (default: False).

    Returns
    -------
    str
        JSON string describing the removal result.
    """
    try:
        if force:
            try:
                handle = await asyncio.to_thread(microsandbox.Sandbox.get, name)
                await asyncio.to_thread(handle.kill)
            except Exception:
                pass
        await asyncio.to_thread(microsandbox.Sandbox.remove, name)
        return json.dumps({"name": name, "removed": True}, ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_remove failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
