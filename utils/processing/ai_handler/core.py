"""Core AI orchestration and response generation module."""

import logging
import json
from typing import Dict, Any

from utils.ai.chat import chat
from utils.config.app_config import LOGGER_NAME, get_base_preprompt
from utils.processing.ai_handler.attachments import process_attachments
from utils.processing.ai_handler.conversation import get_conversation_history
from utils.memory import initialize, get_memory_manager
from utils.database.user_config import get_perso_preprompt

logger = logging.getLogger(LOGGER_NAME)


async def generate_response(
    user_id: int,
    server_id: int,
    raw_content: str,
    attachments: list,
    bot,
    user,
    parameters: Dict[str, Any]
) -> Dict[str, Any] | str:
    """Generate AI response with full pipeline orchestration."""
    try:
        if not getattr(initialize, '_initialized', False):
            await initialize()
            initialize._initialized = True

        logger.info(f"Starting response generation for user {user} (ID: {user_id})")

        processed_content = await process_attachments(raw_content, attachments)
        logger.debug(f"Content processed: {processed_content[:200]}...")

        perso_preprompt = get_perso_preprompt(user_id) if get_perso_preprompt(user_id) else ""

        history_context = {"stm": [], "ltm": ""}
        if parameters.get("history", True):
            logger.debug("Retrieving conversation history")
            history_context = await get_conversation_history(user_id, server_id, processed_content)

        preprompt = get_base_preprompt()
        if parameters.get("preprompt", True) and perso_preprompt:
            preprompt += f"\n\n{perso_preprompt}"

        messages = await _build_messages(processed_content, preprompt, history_context)

        logger.debug(f"Calling chat model with {len(messages)} messages")
        response = await chat(messages, bot, user, parameters)

        if not isinstance(response, bytes) and parameters.get("history", True):
            try:
                if isinstance(response, dict) and 'response' in response:
                    response_text = response['response']
                    combined = {
                        "user": processed_content,
                        "assistant": response_text
                    }
                    manager = get_memory_manager()
                    await manager.add_conversation_message(
                        int(user_id),
                        int(server_id),
                        json.dumps(combined, ensure_ascii=False),
                        role="conversation"
                    )
                    logger.debug("Memory updated with conversation")
            except Exception as e:
                logger.error(f"Failed to update memory: {str(e)}")

        return response

    except Exception as e:
        logger.error(f"Critical error in response generation: {str(e)}", exc_info=True)
        return "An unexpected error occurred. Please try again."


async def _build_messages(
    user_input: str,
    system_prompt: str,
    history: Dict[str, Any] = None
) -> list[Dict[str, str]]:
    """Build message list for AI model.
    
    Args:
        user_input: The user's current input
        system_prompt: The system prompt/preprompt
        history: Dict with 'stm' (list of dicts) and 'ltm' (text string)
    """
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Handle history if provided
    if history:
        # Add LTM as system context if present
        if isinstance(history, dict):
            ltm_text = history.get("ltm", "")
            if ltm_text and isinstance(ltm_text, str) and ltm_text.strip():
                messages.append({
                    "role": "system",
                    "content": f"Previous conversation context:\n{ltm_text}"
                })
            
            # Add STM as message dictionaries (keep as-is)
            stm = history.get("stm", [])
            if isinstance(stm, list):
                for msg in stm:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        messages.append(msg)
        elif isinstance(history, str) and history.strip():
            # Fallback for backward compatibility
            messages.append({
                "role": "system",
                "content": f"Previous conversation context:\n{history}"
            })
        elif isinstance(history, list):
            # Fallback for backward compatibility
            messages.extend(history)

    messages.append({"role": "user", "content": user_input})
    return messages
