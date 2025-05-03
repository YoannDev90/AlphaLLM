import sys
import os
import asyncio
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.openai import openai
from models.openai_large import openai_large
from models.deepseek_reasoning import deepseek_reasoning
from models.deepseek import deepseek
from models.evil import evil
from models.llama import llama
from models.mistral import mistral
from models.phi import phi
from models.qwen_coder import qwen_coder
from models.searchgpt import searchgpt

logger = logging.getLogger('AlphaLLM')

MODELS = [openai, openai_large, deepseek_reasoning, deepseek, evil, llama, mistral, phi, qwen_coder, searchgpt]

async def test_model(model_func):
    prompt = "Just answer 'Online' to check if the model is online."
    try:
        result = await model_func(prompt)
        if "online" in result.lower():
            logger.info(f"{model_func.__name__} works")
            return True
    except Exception as e:
        logger.error(f"{model_func.__name__} error: {str(e)}")
        return str(e)

async def test_models():
    # Crée une liste de coroutines pour tous les modèles
    tasks = [test_model(model) for model in MODELS]
    # Lance-les toutes en parallèle et récupère les résultats
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        print(result)
    if any(result is not True for result in results):
        return "Some models failed"
    return "All models tested"

if __name__ == "__main__":
    print(asyncio.run(test_models()))
