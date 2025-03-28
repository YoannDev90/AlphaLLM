import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.openai import openai
from models.openai_large import openai_large

import asyncio
import logging

logger = logging.getLogger('AlphaLLM')

MODELS = [
    {"name": openai, "description": "OpenAI model"},
    {"name": openai_large, "description": "OpenAI large model"}
]

async def test_model(model_func):
    prompt = "Answer 'Online'"
    try:
        result = await model_func(prompt)
        if "online" in result.lower():
            logger.info(f"{model_func.__name__} works")
            return f"{model_func.__name__} works"
    except Exception as e:
        logger.error(f"{model_func.__name__} error: {str(e)}")
        return str(e)

async def test_models():
    for model in MODELS:
        result = await test_model(model["name"])
        print(result)
    return "All models tested"

if __name__ == "__main__":
    print(asyncio.run(test_models()))