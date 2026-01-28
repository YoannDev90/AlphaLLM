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
    except:
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
    start_time = time.time()
    while not shutdown_event.is_set():
        for model in AVAILABLE_MODELS:
            if model == "evilgpt":
                continue  # Skip evilgpt as its status is the same as mistral's
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
                if results:
                    logger.debug(f"Status check for {model}: success")
                else:
                    logger.debug(f"Status check for {model}: no response")
            except Exception as e:
                logger.error(f"Status check failed for {model}: {e}")
            await asyncio.sleep(5 * 60)
        elapsed = time.time() - start_time
        sleep_time = 8 * 3600 - elapsed
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        start_time = time.time()


def get_status() -> Dict[str, Dict[str, Any]]:
    """Return the latest status dictionary for all bots."""
    status = load_status()
    if "mistral" in status and "evilgpt" in status:
        status["evilgpt"] = status["mistral"].copy()
    return status
