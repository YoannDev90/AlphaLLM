"""Content enhancement functions for AI operations."""

import logging
import asyncio
import json
import requests

import litellm

from utils.config.app_config import (
    LOGGER_NAME,
    IMAGE_ENHANCER_PREPROMPT,
    CF_WORKERS_ACC_ID,
    CF_WORKERS_API_KEY,
    API_ENDPOINTS_OTHER,
    AIML_API_KEY,
    MAX_TOKENS_IMAGE_DESCRIPTION
)

logger = logging.getLogger(LOGGER_NAME)

# Models for prompt enhancement
ENHANCEMENT_MODELS = ["groq/llama-3.1-8b-instant", "cerebras/llama3.1-8b"]


async def enhance_image_prompt(original_prompt: str, number: int = 2) -> dict:
    """Enhance image generation prompt with multiple models."""
    try:
        tasks = []
        
        for i in range(min(number, 4)):
            model = ENHANCEMENT_MODELS[i % len(ENHANCEMENT_MODELS)]
            messages = [
                {"role": "system", "content": IMAGE_ENHANCER_PREPROMPT},
                {"role": "user", "content": original_prompt}
            ]
            task = litellm.acompletion(model=model, messages=messages)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        result = {}
        for i, response in enumerate(results, 1):
            result[i] = response.choices[0].message.content
        
        return result
        
    except Exception as e:
        logger.error(f"Error enhancing prompt: {str(e)}")
        return {1: original_prompt}


def summarize(input_text: str, max_length: int = 100) -> str:
    """Summarize text using Cloudflare AI."""
    try:
        cloudflare_base = API_ENDPOINTS_OTHER.get(
            "cloudflare_ai",
            "https://api.cloudflare.com/client/v4/accounts"
        )
        url = f"{cloudflare_base}/{CF_WORKERS_ACC_ID}/ai/run/@cf/facebook/bart-large-cnn"
        headers = {
            "Authorization": f"Bearer {CF_WORKERS_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "input_text": input_text,
            "parameters": {"max_length": max_length}
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['result']['summary']
        
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        return input_text[:max_length]


def describe_image(image_url: str) -> dict:
    """Get image description using vision model."""
    try:
        url = API_ENDPOINTS_OTHER.get("aiml", "https://api.aimlapi.com/chat/completions")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {AIML_API_KEY}'
        }
        payload = json.dumps({
            "model": "meta-llama/Llama-Vision-Free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image"},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            "max_tokens": MAX_TOKENS_IMAGE_DESCRIPTION
        })

        response = requests.post(url, headers=headers, data=payload, timeout=30)
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        logger.error(f"Image description error: {str(e)}")
        return {"error": str(e)}
