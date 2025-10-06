import logging
from utils.config import logger_name, API_ENDPOINTS_TEXT, MODELS_CONFIG_TEXT, NAVY_API_KEY
from dotenv import load_dotenv
import os
import litellm
from datetime import datetime
from litellm.integrations.opik.opik import OpikLogger
import os

logger = logging.getLogger(logger_name)

load_dotenv()

async def grok_chat(messages, parameters):
    start_time = datetime.now()
    opik_logger = OpikLogger()
    litellm.callbacks = [opik_logger]

    params = {
        "model": MODELS_CONFIG_TEXT.get("grok", "openai/grok-3"),
        "api_key": NAVY_API_KEY,
        "base_url": API_ENDPOINTS_TEXT.get("navy", "https://api.navy/v1"),
        "messages": messages
    }
    
    response = litellm.completion(**params)

    usage = response.usage.total_tokens
    model = response.model

    response_text = response.choices[0].message.content
    
    end_time = datetime.now()
    elapsed_time = end_time - start_time
    minutes = elapsed_time.seconds // 60
    seconds = elapsed_time.seconds % 60
    milliseconds = elapsed_time.microseconds // 1000
    
    if minutes > 0:
        elapsed_time_str = f"{minutes} minutes, {seconds}.{milliseconds:03d} seconds"
    else:
        elapsed_time_str = f"{seconds}.{milliseconds:03d} seconds"

    response_info = {
        "response": response_text,
        "usage": usage,
        "model": model,
        "elapsed_time": elapsed_time_str
    }

    if parameters["raw"]:
        return response_info
    else:
        return response_info
