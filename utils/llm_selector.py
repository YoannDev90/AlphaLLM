import logging
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

async def llm_selector(input):
    
    models_text = await models("text")
    
    messages = [
        {"role": "system", "content": get_llm_selector_preprompt() + models_text},
        {"role": "user", "content": input}
    ]
       
    response = requests.post(
        API_ENDPOINTS_TEXT.get("hackclub", "https://ai.hackclub.com/chat/completions"),
        headers={
            "Content-Type": "application/json",
        },
        json={
            "model": MODELS_CONFIG_TEXT.get("llm_selector", "openai/gpt-oss-20b"),
            "messages": messages
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        text = data["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API error: {response.status_code} {response.text}")
    
    model = await parse_llm_selection(text)
    return model

async def parse_llm_selection(text):
    t = text.lower()
    available_models = await models("json")
    for model_name in available_models.keys():
        if model_name.lower() in t:
            return model_name
    return "cerebras/llama3.3-70b"
    