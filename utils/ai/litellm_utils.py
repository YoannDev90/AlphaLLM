"""Utilities for handling litellm errors and API calls."""

import json
import logging
import re
import litellm
from typing import Any, Dict

logger = logging.getLogger(__name__)


def extract_litellm_error_message(error: Exception) -> str:
    """Extract readable error message from litellm exceptions.
    
    Args:
        error: The exception raised by litellm
        
    Returns:
        str: Human-readable error message
    """
    try:
        error_str = str(error)
        
        # Try to extract JSON error message (from provider API response)
        if '{"object":"error"' in error_str:
            try:
                json_start = error_str.find('{"object":"error"')
                json_end = error_str.find('}', json_start) + 1
                if json_start != -1 and json_end > json_start:
                    error_json = json.loads(error_str[json_start:json_end])
                    if 'message' in error_json:
                        return error_json['message']
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Try to extract from error attributes if available
        if hasattr(error, 'message') and error.message:
            return str(error.message)
        
        # Try different error type patterns
        error_patterns = [
            ('RateLimitError:', 'RateLimitError'),
            ('APIError:', 'APIError'),
            ('APIConnectionError:', 'APIConnectionError'),
            ('MistralException -', 'MistralException'),
        ]
        
        for pattern, error_type in error_patterns:
            if pattern in error_str:
                parts = error_str.split(pattern)
                if len(parts) > 1:
                    msg = parts[-1].strip()
                    # Remove leading "litellm." prefix if present
                    if msg.startswith('litellm.'):
                        msg = msg[8:].strip()
                    # Clean up the message (remove extra info)
                    if msg and msg[0] in ['{', '"']:
                        # If it's JSON or quoted, try to parse it
                        try:
                            # Try to find the actual message within the JSON
                            match = re.search(r'"message"\s*:\s*"([^"]+)"', msg)
                            if match:
                                return match.group(1)
                        except:
                            pass
                    return msg
        
        # Fallback: return the original error string, but clean it up
        # Remove "litellm.RateLimitError: " prefix if present
        if error_str.startswith('litellm.'):
            error_str = error_str[8:]
        if ':' in error_str:
            error_str = error_str.split(':', 1)[-1].strip()
        
        return error_str if error_str else "Unknown API error"
        
    except Exception:
        return str(error)


def handle_litellm_error(error: Exception, model: str = "unknown") -> Dict[str, Any]:
    """Handle litellm errors and return appropriate response.
    
    Args:
        error: The exception from litellm
        model: The model name that failed
        
    Returns:
        Dict: Error response in standard format
    """
    error_msg = extract_litellm_error_message(error)
    logger.error(f"LLM API error for model {model}: {error_msg}")
    
    return {
        "response": f"API Error: {error_msg}",
        "usage": 0,
        "model": "error",
        "elapsed_time": "0 seconds"
    }
