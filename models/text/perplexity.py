import litellm
from litellm.integrations.opik.opik import OpikLogger
from datetime import datetime
import os
import re
from utils.config import API_ENDPOINTS_TEXT, MODELS_CONFIG_TEXT, NAVY_API_KEY

async def perplexity_chat(messages, parameters):
    start_time = datetime.now()
    opik_logger = OpikLogger()
    litellm.callbacks = [opik_logger]
    
    params = {
        "model": MODELS_CONFIG_TEXT.get("perplexity", "openai/sonar"),
        "api_key": NAVY_API_KEY,
        "base_url": API_ENDPOINTS_TEXT.get("navy", "https://api.navy/v1"),
        "messages": messages
    }
    
    response = litellm.completion(**params)

    usage = response.usage.total_tokens
    model = response.model

    response_text = response.choices[0].message.content
    sources = response.citations if hasattr(response, 'citations') and response.citations else []
    
    def replace_citation(match):
        citation_num = int(match.group(1))
        if 1 <= citation_num <= len(sources):
            return f" [[{citation_num}]](<{sources[citation_num - 1]}>)"
        return match.group(0)
    response_text = re.sub(r'\[(\d+)\]', replace_citation, response_text)

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