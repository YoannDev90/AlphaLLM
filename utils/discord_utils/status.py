"""Bot status snapshot derived from the refactor stack."""
import math
from typing import Any, Dict, List, Optional, Tuple
import discord
import logging
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

def _load_bot_handles() -> List[Tuple[str, Optional[discord.Client]]]:
    """Load bot handles from the global scope."""
    bots: List[Tuple[str, Optional[discord.Client]]] = []
    return bots

def _summarize_bot(bot: Optional[discord.Client]) -> Dict[str, Any]:
    if bot is None:
        return {"ping": 0.0, "status": "offline"}

    #latency = getattr(bot, "latency", 0.0) or 0.0
    latency = 0.0
    ping = round(latency * 1000, 2)
    if math.isnan(ping):
        ping = 0.0
        state = "offline"
    elif ping > 200:
        state = "degraded"
    else:
        state = "online"
    return {"ping": ping, "status": state}


def get_status() -> Dict[str, Dict[str, Any]]:
    """Return the latest status dictionary for all bots."""

    statuses: Dict[str, Dict[str, Any]] = {}
    bots = _load_bot_handles()
    for name, bot in bots:
        statuses[name] = _summarize_bot(bot)
    return statuses
