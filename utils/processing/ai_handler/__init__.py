"""AI response handler sub-package with modular orchestration."""

from utils.processing.ai_handler.attachments import process_attachments
from utils.processing.ai_handler.conversation import get_conversation_history, search_memory
from utils.processing.ai_handler.core import generate_response, _build_messages
from utils.processing.ai_handler.discord_handler import process_ai_response
from utils.processing.ai_handler.enhancement import (
    enhance_image_prompt,
    describe_image,
    summarize,
)

# Alias for backward compatibility
async def messages_builder(user_input, system_prompt, perso_preprompt, history):
    """Build messages for AI model (backward compatibility wrapper)."""
    if perso_preprompt:
        system_prompt += f"\n\n{perso_preprompt}"
    return await _build_messages(user_input, system_prompt, history)

__all__ = [
    "process_attachments",
    "get_conversation_history",
    "search_memory",
    "generate_response",
    "process_ai_response",
    "enhance_image_prompt",
    "describe_image",
    "summarize",
    "messages_builder",
]
