"""Bot status snapshot derived from the refactor stack."""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import discord

from config import LOGGER_NAME, AVAILABLE_MODELS

logger = logging.getLogger(LOGGER_NAME)

def get_status() -> Dict[str, Dict[str, Any]]:
    """Return the latest status dictionary for all bots."""

    status = {}
    for model in AVAILABLE_MODELS:
        status[model] = "online"
    return status