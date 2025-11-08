import logging
from utils.config.app_config import logger_name
from dotenv import load_dotenv
import os
import requests
import json
import asyncio

logger = logging.getLogger(logger_name)

load_dotenv()

async def conversation_title(input_text: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    api_key = os.getenv("GROQ_API_KEY")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {
                "role": "system",
                "content": "Output only a 3 words title using the same language as the user, nothing else. Example: 'Minecraft Server Setup'."
            },
            {
                "role": "user",
                "content": input_text
            }
        ],
        "temperature": 0,
        "reasoning_effort":"low",
        "max_tokens": 256
    }

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, lambda: requests.post(url, headers=headers, json=data))
        response.raise_for_status()
        result = response.json()
        response_text = result["choices"][0]["message"]["content"]
        return response_text
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error: {e}"
