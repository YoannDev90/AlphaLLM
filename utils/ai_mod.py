from jigsawstack import JigsawStack
import os
import requests
from dotenv import load_dotenv
from config import MODERATION_API_KEY
import logging

load_dotenv()

JIGSAWSTACK_API_KEY = os.getenv("NSFW_CLASSIFIER_API_KEY")

jigsaw = JigsawStack(api_key=JIGSAWSTACK_API_KEY)

logger = logging.getLogger(__name__)

def is_nsfw(image_url: str) -> dict:
    """
    Check if an image is NSFW using JigsawStack API.
    
    Args:
        image_url (str): URL of the image to check
        
    Returns:
        dict: {
            'success': bool,
            'nsfw': bool or None,
            'error': str or None
        }
    """
    try:
        response = jigsaw.validate.nsfw({"url": image_url})
        nsfw = response.get("nsfw", False) or response.get("nudity", False)
        return {
            'success': True,
            'nsfw': nsfw,
            'error': None
        }
    except Exception as e:
        logger.error(f"Error checking NSFW for {image_url}: {str(e)}")
        return {
            'success': False,
            'nsfw': None,
            'error': str(e)
        }

def moderate(text: str) -> dict:
    """
    Moderate text using Naga API via requests.
    
    Args:
        text (str): Text to moderate
        
    Returns:
        dict: {
            'success': bool,
            'flagged': bool or None,
            'categories': dict or None,
            'error': str or None
        }
    """
    try:
        url = "https://api.naga.ac/v1/moderations"
        headers = {
            "Authorization": f"Bearer {MODERATION_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "omni-moderation-latest",
            "input": text
        }
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            resp_json = response.json()
            if 'results' in resp_json and resp_json['results']:
                result = resp_json['results'][0]
                return {
                    'success': True,
                    'flagged': result.get('flagged'),
                    'categories': result.get('categories'),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'flagged': None,
                    'categories': None,
                    'error': 'Invalid response structure'
                }
        else:
            return {
                'success': False,
                'flagged': None,
                'categories': None,
                'error': f'HTTP {response.status_code}: {response.text}'
            }
            
    except Exception as e:
        logger.error(f"Error moderating text: {str(e)}")
        return {
            'success': False,
            'flagged': None,
            'categories': None,
            'error': str(e)
        }