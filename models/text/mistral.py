import logging
from utils.config import logger_name
from dotenv import load_dotenv
import os
import litellm
from datetime import datetime
from litellm.integrations.opik.opik import OpikLogger
import os
import json

logger = logging.getLogger(logger_name)

load_dotenv()

async def mistral_chat(messages, parameters):
    start_time = datetime.now()
    opik_logger = OpikLogger()
    litellm.callbacks = [opik_logger]

    with open("models/text/mistral_config.json", "r") as f:
        mistral_configs = json.load(f)
    
    primary_config = mistral_configs[0]["litellm_params"]
    fallback_configs = [config["litellm_params"] for config in mistral_configs[1:]]
    
    params = {
        "model": primary_config["model"],
        "api_key": os.getenv(primary_config["api_key"]),
        "messages": messages
    }
    
    if "api_base" in primary_config:
        params["api_base"] = primary_config["api_base"]
    
    fallbacks = []
    for fb_config in fallback_configs:
        fb_params = {
            "model": fb_config["model"],
            "api_key": os.getenv(fb_config["api_key"])
        }
        if "api_base" in fb_config:
            fb_params["api_base"] = fb_config["api_base"]
        fallbacks.append(fb_params)
    
    if fallbacks:
        params["fallbacks"] = fallbacks
    
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
