"""Content moderation module for NSFW detection and text analysis."""

import logging
import os
import requests
from typing import Dict, Any

from dotenv import load_dotenv
from jigsawstack import JigsawStack

from utils.config.app_config import LOGGER_NAME, MODERATION_API_KEY
from utils.config.constants import (
    MODERATION_API_URL,
    MODERATION_MODEL,
    MODERATION_TIMEOUT
)

logger = logging.getLogger(LOGGER_NAME)
load_dotenv()

JIGSAWSTACK_API_KEY = os.getenv("NSFW_CLASSIFIER_API_KEY")
jigsaw = JigsawStack(api_key=JIGSAWSTACK_API_KEY)


def is_nsfw(image_url: str) -> Dict[str, Any]:
    """Check if image contains NSFW content using JigsawStack API.
    
    Args:
        image_url: URL of image to analyze.
        
    Returns:
        Dict with keys:
            - success (bool): Whether API call succeeded.
            - nsfw (bool|None): True if NSFW detected.
            - error (str|None): Error message if failed.
            
    Example:
        >>> result = is_nsfw("https://example.com/image.jpg")
        >>> if result['success'] and result['nsfw']:
        ...     print("NSFW content detected")
    """
    try:
        logger.debug(f"Checking NSFW for image: {image_url}")
        response = jigsaw.validate.nsfw({"url": image_url})
        
        nsfw = response.get("nsfw", False) or response.get("nudity", False)
        logger.debug(f"NSFW check result: {nsfw}")
        
        return {
            'success': True,
            'nsfw': nsfw,
            'error': None
        }
    except Exception as e:
        logger.error(f"NSFW check failed for {image_url}: {str(e)}")
        return {
            'success': False,
            'nsfw': None,
            'error': str(e)
        }


def moderate(text: str) -> Dict[str, Any]:
    """Analyze text for potentially harmful content.
    
    Uses Naga API to moderate user-generated text and classify violations
    across multiple categories (hate, harassment, violence, etc.).
    
    Args:
        text: Text content to moderate.
        
    Returns:
        Dict with keys:
            - success (bool): Whether moderation API call succeeded.
            - flagged (bool|None): True if content violates policies.
            - categories (dict|None): Breakdown of violation categories.
            - error (str|None): Error message if failed.
            
    Example:
        >>> result = moderate("User message content here")
        >>> if result['flagged']:
        ...     print(f"Content flagged: {result['categories']}")
    """
    try:
        logger.debug(f"Moderating text ({len(text)} chars)")
        
        headers = {
            "Authorization": f"Bearer {MODERATION_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODERATION_MODEL,
            "input": text
        }
        
        response = requests.post(
            MODERATION_API_URL,
            headers=headers,
            json=payload,
            timeout=MODERATION_TIMEOUT
        )
        
        if response.status_code == 200:
            resp_json = response.json()
            
            if 'results' in resp_json and resp_json['results']:
                result = resp_json['results'][0]
                flagged = result.get('flagged', False)
                categories = result.get('categories', {})
                
                logger.debug(f"Moderation result - flagged: {flagged}")
                
                return {
                    'success': True,
                    'flagged': flagged,
                    'categories': categories,
                    'error': None
                }
            else:
                logger.warning("Unexpected moderation API response structure")
                return {
                    'success': False,
                    'flagged': None,
                    'categories': None,
                    'error': 'Invalid response format'
                }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"Moderation API error: {error_msg}")
            return {
                'success': False,
                'flagged': None,
                'categories': None,
                'error': error_msg
            }
            
    except Exception as e:
        logger.error(f"Text moderation failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'flagged': None,
            'categories': None,
            'error': str(e)
        }
