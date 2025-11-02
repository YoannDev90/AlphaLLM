import logging
from utils.config import logger_name, MODELS_CONFIG_TEXT, CEREBRAS_API_KEY
from dotenv import load_dotenv
import os
import litellm
from datetime import datetime
from litellm.integrations.opik.opik import OpikLogger
import os
import json

logger = logging.getLogger(logger_name)

load_dotenv()

async def llama_chat(messages, parameters):
    try:        
        start_time = datetime.now()
        opik_logger = OpikLogger()
        litellm.callbacks = [opik_logger]

        # Load Llama configurations
        with open("models/text/llama_config.json", "r") as f:
            llama_configs = json.load(f)
        
        primary_config = llama_configs[0]["litellm_params"]
        
        params = {
            "model": primary_config["model"],
            "api_key": os.getenv(primary_config["api_key"]),
            "messages": messages
        }
        
        if "api_base" in primary_config:
            params["api_base"] = primary_config["api_base"]
        
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
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à Llama : {e}")
        logger.error(f"Type d'erreur: {type(e).__name__}")
        return {
            "response": f"Erreur lors de l'appel à Llama : {e}",
            "usage": 0,
            "model": "error",
            "elapsed_time": "0 seconds"
        }
