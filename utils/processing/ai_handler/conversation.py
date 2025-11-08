"""Conversation history and memory retrieval module."""

import logging
from typing import Dict, Any

from utils.config.app_config import LOGGER_NAME
from utils.memory import get_memory_manager

logger = logging.getLogger(LOGGER_NAME)


async def get_conversation_history(
    user_id: int,
    server_id: int,
    current_query: str = ""
) -> Dict[str, Any]:
    """Retrieve relevant conversation history from memory.
    
    Returns:
        Dict with 'stm' (list of dicts) and 'ltm' (text string)
    """
    try:
        logger.debug(f"Retrieving history for user {user_id}")
        
        manager = get_memory_manager()
        if current_query.strip():
            logger.debug(f"Performing hybrid search for query")
            result = await manager.get_hybrid_memories(user_id, server_id, current_query)
            stm = result.get("stm", [])
            ltm = result.get("ltm", [])
            logger.debug(f"Hybrid history loaded: {len(stm)} STM, {len(ltm)} LTM entries")
        else:
            logger.debug("Using chronological history")
            result = await manager.get_memories(user_id, server_id)
            stm = result.get("stm", [])
            ltm = result.get("ltm", [])
            logger.debug(f"Chronological history loaded: {len(stm)} STM, {len(ltm)} LTM entries")

        if not stm and not ltm:
            logger.debug(f"No history found for user {user_id}")
            return {"stm": [], "ltm": ""}
        
        # Build LTM as text string
        ltm_text = "\n".join([f"[{entry['created_at']}] {entry['text']}" for entry in ltm[:10]]) if ltm else ""
        
        return {
            "stm": stm[:10],  # Keep as list of dictionaries
            "ltm": ltm_text    # Convert to text string
        }
        
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}", exc_info=True)
        return {"stm": [], "ltm": ""}


async def search_memory(
    user_id: int,
    server_id: int,
    query: str,
    limit: int = 5
) -> str:
    """Search memory and return formatted results."""
    try:
        manager = get_memory_manager()
        result = await manager.search_memories(user_id, server_id, query, limit)
        memories = result.get("stm", []) + result.get("ltm", [])
        
        if not memories:
            return "No similar memories found."
        
        formatted_results = []
        for i, memory in enumerate(memories, 1):
            formatted_results.append(
                f"{i}. [{memory.get('created_at', 'N/A')}]\n{memory.get('text') or memory.get('content', 'N/A')}"
            )
        
        return "\n\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Memory search error: {str(e)}")
        return f"Search error: {str(e)}"
