"""Bot status snapshot derived from the refactor stack."""

import asyncio
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import discord

from config import AVAILABLE_MODELS, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

STATUS_FILE = Path("data/status.json")


def load_status() -> Dict[str, Dict[str, Any]]:
    """Load status from JSON file."""
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load status: {e}")
    return {}


def save_status(status: Dict[str, Dict[str, Any]]):
    """Save status to JSON file."""
    try:
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save status: {e}")


def update_status_on_success(model: str, elapsed_time: str):
    """Update status for a successful request."""
    if model == "evilgpt":
        model = "mistral"  # evilgpt uses mistral backend
    status = load_status()
    if model not in status:
        status[model] = {
            "status": "unknown",
            "success_rate": 0.0,
            "uptime": 0.0,
            "last_check": 0,
            "total_requests": 0,
            "successful_requests": 0,
        }
    entry = status[model]
    entry["total_requests"] += 1
    entry["successful_requests"] += 1
    entry["last_check"] = time.time()
    entry["success_rate"] = (
        entry["successful_requests"] / entry["total_requests"]
    ) * 100
    try:
        elapsed = float(elapsed_time.split()[0])
        entry["status"] = "online" if elapsed < 30 else "degraded"
    except Exception:
        entry["status"] = "online"
    save_status(status)


def update_status_on_failure(model: str):
    """Update status for a failed request."""
    if model == "evilgpt":
        model = "mistral"  # evilgpt uses mistral backend
    status = load_status()
    if model not in status:
        status[model] = {
            "status": "unknown",
            "success_rate": 0.0,
            "uptime": 0.0,
            "last_check": 0,
            "total_requests": 0,
            "successful_requests": 0,
        }
    entry = status[model]
    entry["total_requests"] += 1
    entry["last_check"] = time.time()
    entry["success_rate"] = (
        (entry["successful_requests"] / entry["total_requests"]) * 100
        if entry["total_requests"] > 0
        else 0.0
    )
    entry["status"] = "offline"
    save_status(status)


async def status_emulation(shutdown_event: asyncio.Event):
    """Émule une requête pour chaque modèle toutes les 5 minutes, en recommençant le cycle toutes les 8 heures"""
    import time

    from utils.unified_text import Origin, unified_text_gen

    await asyncio.sleep(10 * 60)
    status = load_status()
    cycle = status.get("cycle", {})
    current_time = time.time()
    models = [m for m in AVAILABLE_MODELS if m != "evilgpt"]

    if cycle and current_time - cycle.get("start_time", 0) < 8 * 3600:
        # Resume cycle
        current_index = cycle.get("current_index", 0)
        start_time = cycle["start_time"]
        logger.info(f"Resuming status cycle from index {current_index}")
    else:
        # Start new cycle
        current_index = 0
        start_time = current_time
        cycle = {"start_time": start_time, "current_index": current_index}
        status["cycle"] = cycle
        save_status(status)
        logger.info("Starting new status cycle")

    while not shutdown_event.is_set():
        for i in range(current_index, len(models)):
            model = models[i]
            try:
                results = [
                    r
                    async for r in unified_text_gen(
                        user_id=0,
                        conv_id=f"status_check_n{random.randint(0, 1000000)}",
                        input="Say OK",
                        model=model,
                        origin=Origin.STATUS_CHECK,
                        use_memory=False,
                    )
                ]
                if results and len(results) > 0:
                    response_text = (
                        results[0].response
                        if hasattr(results[0], "response")
                        else str(results[0])
                    )
                    # Check if it's an error response
                    error_messages = [
                        "Request timed out",
                        "I'm sorry, but I couldn't generate a response",
                        "API configuration error",
                        "Request timed out after trying all available models",
                    ]
                    is_error = any(
                        error_msg in response_text for error_msg in error_messages
                    )
                    if not is_error:
                        logger.debug(f"Status check for {model}: success")
                    else:
                        logger.debug(
                            f"Status check for {model}: error response - {response_text[:50]}..."
                        )
                else:
                    logger.debug(f"Status check for {model}: no response")
            except Exception as e:
                logger.error(f"Status check failed for {model}: {e}")
            
            # Update cycle index
            cycle["current_index"] = i + 1
            status["cycle"] = cycle
            save_status(status)
            
            await asyncio.sleep(5 * 60)
        
        # Cycle completed, wait for next cycle
        elapsed = current_time - start_time
        sleep_time = 8 * 3600 - elapsed
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        
        # Start new cycle
        start_time = time.time()
        cycle = {"start_time": start_time, "current_index": 0}
        status["cycle"] = cycle
        save_status(status)
        current_index = 0
        logger.info("Starting new status cycle")


def get_status() -> Dict[str, Dict[str, Any]]:
    """Return the latest status dictionary for all bots."""
    status = load_status()
    if "mistral" in status and "evilgpt" in status:
        status["evilgpt"] = status["mistral"].copy()
    return status
