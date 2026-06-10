"""Create microsandbox instances from the bot's tool interface."""

import asyncio
import json
from typing import Any, Dict, List, Optional

import microsandbox

from utils.logger import get_logger

logger = get_logger()


async def sandbox_create(
    name: str,
    image: str,
    cpus: int = 1,
    memoryMib: int = 512,
    workdir: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    volumes: Optional[List[Dict[str, Any]]] = None,
    patches: Optional[List[Dict[str, Any]]] = None,
    entrypoint: Optional[List[str]] = None,
    hostname: Optional[str] = None,
    maxDuration: Optional[int] = None,
    idleTimeout: Optional[int] = None,
) -> str:
    """Create a new sandbox and return a status payload.

    Parameters
    ----------
    name : str
        Sandbox name.
    image : str
        Container image to use.
    cpus : int
        Number of CPUs to allocate (default: 1).
    memoryMib : int
        Memory limit in MiB (default: 512).
    workdir : Optional[str]
        Working directory inside the sandbox (default: None).
    env : Optional[Dict[str, str]]
        Environment variables to inject (default: None).
    volumes : Optional[List[Dict[str, Any]]]
        Volume mounts to configure (default: None).
    patches : Optional[List[Dict[str, Any]]]
        Patch entries to apply (default: None).
    entrypoint : Optional[List[str]]
        Custom entrypoint command (default: None).
    hostname : Optional[str]
        Optional hostname to assign (default: None).
    maxDuration : Optional[int]
        Maximum sandbox duration in seconds (default: None).
    idleTimeout : Optional[int]
        Idle timeout in seconds (default: None).

    Returns
    -------
    str
        JSON string describing the created sandbox.
    """
    try:
        kwargs: Dict[str, Any] = {
            "image": image,
            "cpus": cpus,
            "memory_mib": memoryMib,
        }
        if workdir:
            kwargs["workdir"] = workdir
        if env:
            kwargs["env"] = env
        if entrypoint:
            kwargs["entrypoint"] = entrypoint
        if hostname:
            kwargs["hostname"] = hostname
        if maxDuration is not None:
            kwargs["max_duration"] = maxDuration
        if idleTimeout is not None:
            kwargs["idle_timeout"] = idleTimeout
        if volumes:
            kwargs["volumes"] = volumes
        if patches:
            kwargs["patches"] = patches

        try:
            await asyncio.to_thread(microsandbox.Sandbox.create, name, **kwargs)
        except Exception:
            cfg = {
                "name": name,
                "image": image,
                "cpus": cpus,
                "memoryMib": memoryMib,
                "workdir": workdir,
                "env": env,
                "volumes": volumes,
                "patches": patches,
                "entrypoint": entrypoint,
                "hostname": hostname,
                "maxDuration": maxDuration,
                "idleTimeout": idleTimeout,
            }
            cfg = {k: v for k, v in cfg.items() if v is not None}
            await asyncio.to_thread(microsandbox.Sandbox.create, cfg)

        return json.dumps(
            {"name": name, "status": "running", "image": image},
            ensure_ascii=True,
            indent=2,
        )
    except Exception as exc:
        logger.error("sandbox_create failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
