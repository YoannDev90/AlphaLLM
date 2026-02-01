import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, List

import litellm
import requests

from config import LOGGER_NAME, read_file

logger = logging.getLogger(LOGGER_NAME)

IMG_GEN_ENHANCER_PREPROMPT = read_file("configs/prompts/img_gen_enhancer.txt")
IMG_EDIT_ENHANCER_PREPROMPT = read_file("configs/prompts/img_edit_enhancer.txt")
CONV_NAME_PREPROMPT = read_file("configs/prompts/conv_name.txt")


def load_configs(config_path: str) -> List[Dict[str, Any]]:
    try:
        with open(config_path, "r") as f:
            raw_configs = json.load(f)

        for config in raw_configs:
            litellm_params = config.get("litellm_params", {})
            if "api_base" in litellm_params:
                api_base = litellm_params["api_base"]
                api_base = re.sub(
                    r"<(\w+)>", lambda m: os.environ.get(m.group(1), ""), api_base
                )
                litellm_params["api_base"] = api_base

        return raw_configs
    except Exception as e:
        logger.error(f"Erreur lors du chargement des configs {config_path}: {e}")
        raise


async def enhance_image_prompt(
    original_prompt: str, number: int = 2, is_edit: bool = False, style: str = None
) -> dict:
    """Enhance image generation prompt with multiple models."""
    enhancement_models = load_configs("configs/misc/img_enhancer.json")
    try:
        tasks = []

        if not is_edit:
            system_prompt = IMG_GEN_ENHANCER_PREPROMPT
        else:
            system_prompt = IMG_EDIT_ENHANCER_PREPROMPT
            number = 1

        # Add style instructions if provided
        if style:
            try:
                style_instructions = read_file(f"configs/img_styles/{style}.txt")
                system_prompt += f"\n\n**Style Instructions:**\n{style_instructions}\n\nIncorporate these style characteristics into your enhanced prompt."
            except Exception as e:
                logger.warning(f"Could not load style instructions for {style}: {e}")

        for i in range(min(number, 4)):
            model_config = enhancement_models[i % len(enhancement_models)][
                "litellm_params"
            ]
            model = model_config["model"]
            api_key = os.getenv(model_config["api_key"])
            api_base = model_config.get("api_base")
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": original_prompt},
            ]
            task = litellm.acompletion(
                model=model, messages=messages, api_key=api_key, api_base=api_base
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        result = {}
        for i, response in enumerate(results, 1):
            result[i] = response.choices[0].message.content

        return result

    except Exception as e:
        logger.error(f"Error enhancing prompt: {str(e)}")
        return {1: original_prompt}


def summarize(input_text: str, max_length: int = None) -> str:
    """Summarize text using Cloudflare AI."""

    if max_length is None:
        max_length = len(input_text) // 4
    config = load_configs("configs/misc/summarizer.json")[0]["litellm_params"]

    try:
        api_key = os.getenv(config["api_key"])
        url = f"{config['api_base']}/run/{config['model']}"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"input_text": input_text, "max_length": max_length}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result["result"]["summary"]

    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        return input_text[:max_length]


def conv_name(input_text: str) -> str:
    """Generate a conversation name."""
    conv_name_models = load_configs("configs/misc/conv_name.json")
    try:
        model_config = conv_name_models[0]["litellm_params"]
        model = model_config["model"]
        api_key = os.getenv(model_config["api_key"])
        api_base = model_config.get("api_base")
        messages = [
            {"role": "system", "content": CONV_NAME_PREPROMPT},
            {"role": "user", "content": input_text},
        ]
        fallbacks = [m["litellm_params"]["model"] for m in conv_name_models[1:]]
        response = litellm.completion(
            model=model,
            messages=messages,
            api_key=api_key,
            api_base=api_base,
            fallbacks=fallbacks,
        )
        return response.choices[0].message.content.strip().strip('"')

    except Exception as e:
        logger.error(f"Error generating conversation name: {str(e)}")
        return "Untitled"
