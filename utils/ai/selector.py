"""Intelligent LLM model selection based on user input."""

import logging
import asyncio
import os
import requests
from typing import Dict, List

from dotenv import load_dotenv

from utils.config.app_config import LOGGER_NAME, CONFIG
from utils.config.constants import (
    SELECTOR_ENDPOINTS,
    LLM_SELECTOR_TIMEOUT,
    DEFAULT_MODEL
)

logger = logging.getLogger(LOGGER_NAME)
load_dotenv()


async def _call_llm_api(url: str, headers: Dict, messages: List[Dict]) -> str:
    """Call external LLM API synchronously in thread pool.
    
    Args:
        url: API endpoint URL.
        headers: HTTP headers with authentication.
        messages: OpenAI-format message list.
        
    Returns:
        str: Model selection recommendation from LLM.
        
    Raises:
        Exception: If API call fails.
    """
    def _sync_request():
        response = requests.post(url, headers=headers, json={
            "model": "openai/gpt-oss-20b",
            "messages": messages
        })
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API error {response.status_code}: {response.text}")
    
    return await asyncio.to_thread(_sync_request)


async def llm_selector(user_input: str) -> str:
    """Select best LLM model for user query using cascading fallback chain.
    
    Attempts to call external LLMs in order (OpenRouter → HackClub → IO Intelligence).
    Falls back to 'llama' if all APIs fail.
    
    Args:
        user_input: User's question or request.
        
    Returns:
        str: Selected model name (e.g., 'mistral', 'claude', 'llama').
    """
    # Build model reference list from config
    models_dict = {k: v.get("description", "") for k, v in CONFIG.get("models", {}).items()}
    models_text = "\n".join(f"- {k}: {v}" for k, v in models_dict.items())
    
    system_prompt = f"""Analyze the user query and recommend the best AI model.
Available models:
{models_text}

Respond with ONLY the model name."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    # Cascading fallback chain
    selection_text = None
    
    # Try OpenRouter
    try:
        logger.debug("Attempting LLM selection via OpenRouter")
        headers = {
            "Content-Type": "application/json",
            "Authorization": SELECTOR_ENDPOINTS["openrouter"]["auth_header"]()
        }
        selection_text = await _call_llm_api(
            SELECTOR_ENDPOINTS["openrouter"]["url"],
            headers,
            messages
        )
        logger.debug("OpenRouter selection successful")
    except Exception as e:
        logger.warning(f"OpenRouter failed: {str(e)}")
    
    # Try HackClub
    if not selection_text:
        try:
            logger.debug("Attempting LLM selection via HackClub")
            headers = {"Content-Type": "application/json"}
            selection_text = await _call_llm_api(
                SELECTOR_ENDPOINTS["hackclub"]["url"],
                headers,
                messages
            )
            logger.debug("HackClub selection successful")
        except Exception as e:
            logger.warning(f"HackClub failed: {str(e)}")
    
    # Try IO Intelligence
    if not selection_text:
        try:
            logger.debug("Attempting LLM selection via IO Intelligence")
            headers = {
                "Content-Type": "application/json",
                "Authorization": SELECTOR_ENDPOINTS["io_intelligence"]["auth_header"]()
            }
            selection_text = await _call_llm_api(
                SELECTOR_ENDPOINTS["io_intelligence"]["url"],
                headers,
                messages
            )
            logger.debug("IO Intelligence selection successful")
        except Exception as e:
            logger.warning(f"IO Intelligence failed: {str(e)}")
    
    # Final fallback
    if not selection_text:
        logger.warning("All LLM selector endpoints failed, using Llama fallback")
        return "llama"
    
    # Parse selection response
    model = await _parse_selection(selection_text)
    logger.info(f"Selected model: {model}")
    return model


async def _parse_selection(response_text: str) -> str:
    """Extract model name from LLM response.
    
    Args:
        response_text: LLM's response containing model recommendation.
        
    Returns:
        str: Extracted model name or 'llama' if parsing fails.
    """
    response_lower = response_text.lower()
    available_models = CONFIG.get("models", {}).keys()
    
    for model_name in available_models:
        if model_name.lower() in response_lower:
            return model_name
    
    logger.debug(f"Could not parse model from response: {response_text}")
    return "llama"
