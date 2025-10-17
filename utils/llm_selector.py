import logging
import asyncio
from utils.config import logger_name, get_llm_selector_preprompt, CONFIG, API_ENDPOINTS_TEXT, MODELS_CONFIG_TEXT
from dotenv import load_dotenv
import os
import requests

logger = logging.getLogger(logger_name)

load_dotenv()

async def models(format):   
    models_raw = CONFIG.get("models", {})
    models_dict = {k: v.get("description", "") for k, v in models_raw.items()}
    
    if format == "text":
        return "\n".join(f"- {k} : {v}" for k, v in models_dict.items())
    else:
        return models_dict
    

async def hackclub_llm_selector(messages):
    def _sync_request():
        response = requests.post(
            "https://ai.hackclub.com/chat/completions",
            headers={
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": messages
            }
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"HackClub API error: {response.status_code} {response.text}")
    
    return await asyncio.to_thread(_sync_request)
    
async def io_intelligence_llm(messages):
    def _sync_request():
        response = requests.post(
            "https://api.intelligence.io.solutions/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('IO_INTELLIGENCE_API_KEY')}"
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": messages
                }
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"IO Intelligence API error: {response.status_code} {response.text}")
    
    return await asyncio.to_thread(_sync_request)


async def openrouter_llm_selector(messages):
    def _sync_request():
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": messages
            }
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"OpenRouter API error: {response.status_code} {response.text}")
    
    return await asyncio.to_thread(_sync_request)



async def llm_selector(input):
    
    models_text = await models("text")
    
    messages = [
        {"role": "system", "content": get_llm_selector_preprompt() + models_text},
        {"role": "user", "content": input}
    ]

    try :
        text = await hackclub_llm_selector(messages)
    except Exception as e:
        logger.error(f"HackClub LLM Selector failed: {e}. Falling back to OpenRouter LLM Selector.")
        try:
            text = await openrouter_llm_selector(messages)
        except Exception as e2:
            logger.error(f"OpenRouter LLM Selector failed: {e2}. Falling back to IO Intelligence LLM Selector.")
            try:
                text = await io_intelligence_llm(messages)
            except Exception as e3:
                logger.error(f"IO Intelligence LLM Selector also failed: {e3}. Using default model.")
                return "cerebras/llama3.3-70b"
    
    model = await parse_llm_selection(text)
    return model

async def parse_llm_selection(text):
    t = text.lower()
    available_models = await models("json")
    for model_name in available_models.keys():
        if model_name.lower() in t:
            return model_name
    return "cerebras/llama3.3-70b"
    