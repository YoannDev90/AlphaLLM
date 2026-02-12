import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from config import LOGGER_NAME
from utils.ressources import get_default_monitor
from utils.uptime_monitor import get_uptime_monitor

router = APIRouter()
logger = logging.getLogger(LOGGER_NAME)


def get_realtime_data():
    """Get last 60 seconds of resource data."""
    monitor = get_default_monitor()
    snapshots = monitor.get_all_snapshots()
    recent = snapshots[-60:] if len(snapshots) >= 60 else snapshots

    return [
        {
            "timestamp": s.timestamp.isoformat(),
            "cpu_percent": round(s.cpu_percent, 2) if s.cpu_percent else 0.0,
            "memory_percent": round(s.memory_percent, 2) if s.memory_percent else 0.0,
        }
        for s in recent
    ]


async def event_generator():
    """Generator for Server-Sent Events to stream resource data."""
    while True:
        try:
            realtime = get_realtime_data()
            data = {"realtime": realtime}
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error during resources streaming: {str(e)}")
            yield f'data: {{"error": "{str(e)}"}}\n\n'
            await asyncio.sleep(1)


@router.get("/resources", tags=["general"])
async def resources_check():
    """API resources check endpoint with SSE streaming"""
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/uptime", tags=["general"])
async def uptime_check():
    """Get uptime and availability metrics"""
    monitor = get_uptime_monitor()
    return {
        "uptime": round(monitor.get_current_uptime(), 2),
        "availability_30d": round(monitor.get_availability(30), 2),
        "availability_90d": round(monitor.get_availability(90), 2),
    }
