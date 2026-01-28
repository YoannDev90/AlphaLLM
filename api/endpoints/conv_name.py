import logging
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from api.api_utils.security_utils import get_api_key
from config import LOGGER_NAME
from utils.ai_process.ai_utils import conv_name

router = APIRouter()
logger = logging.getLogger(LOGGER_NAME)


@router.post("/text/conv_name", tags=["text"], summary="Generate conversation title")
async def generate_conversation_name(
    messages: List[Dict[str, str]], api_key: Optional[str] = Depends(get_api_key)
):

    if not messages or len(messages) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages list cannot be empty",
        )

    start_time = time.time()

    valid_messages = []
    roles_seen = set()
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if (
            role in {"system", "user", "assistant"}
            and content
            and role not in roles_seen
        ):
            valid_messages.append({"role": role, "content": content})
            roles_seen.add(role)

    messages_text = "\n".join(
        f"{entry['role']}: {entry['content']}" for entry in valid_messages
    )
    total_chars = sum(len(entry["content"]) for entry in valid_messages)

    try:
        title = conv_name(messages_text)
    except Exception as exc:
        logger.error(f"Unexpected error during conversation name generation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during conversation name generation",
        )

    elapsed_time = time.time() - start_time

    return {
        "status": "success",
        "conversation_title": title,
        "metadata": {
            "messages_count": len(valid_messages),
            "total_characters": total_chars,
            "processing_time": round(elapsed_time, 2),
        },
    }
