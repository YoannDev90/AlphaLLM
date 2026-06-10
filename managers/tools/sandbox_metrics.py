"""Sandbox helper for retrieving resource usage metrics."""

import asyncio
import json

import microsandbox

from utils.logger import get_logger

logger = get_logger()


async def sandbox_metrics(name: str) -> str:
    """Return resource metrics for a sandbox.

    Parameters
    ----------
    name : str
        Sandbox name.

    Returns
    -------
    str
        JSON object string with CPU, memory, disk and network metrics.
    """
    try:
        sandbox = await asyncio.to_thread(microsandbox.Sandbox.get, name)
        metrics = await asyncio.to_thread(sandbox.metrics)
        payload = {
            "cpuPercent": getattr(metrics, "cpu_percent", None)
            or getattr(metrics, "cpuPercent", None),
            "memoryBytes": getattr(metrics, "memory_bytes", None)
            or getattr(metrics, "memoryBytes", None),
            "memoryLimitBytes": getattr(metrics, "memory_limit_bytes", None)
            or getattr(metrics, "memoryLimitBytes", None),
            "diskReadBytes": getattr(metrics, "disk_read_bytes", None)
            or getattr(metrics, "diskReadBytes", None),
            "diskWriteBytes": getattr(metrics, "disk_write_bytes", None)
            or getattr(metrics, "diskWriteBytes", None),
            "netRxBytes": getattr(metrics, "net_rx_bytes", None)
            or getattr(metrics, "netRxBytes", None),
            "netTxBytes": getattr(metrics, "net_tx_bytes", None)
            or getattr(metrics, "netTxBytes", None),
            "uptimeSecs": getattr(metrics, "uptime_secs", None)
            or getattr(metrics, "uptimeSecs", None),
        }
        return json.dumps(payload, ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.error("sandbox_metrics failed: %s", exc, exc_info=True)
        return f"Error: {str(exc)}"
