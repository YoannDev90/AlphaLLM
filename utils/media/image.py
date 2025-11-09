"""Image generation module with multi-model fallback support."""

import base64
import logging
from typing import Literal

from utils.config.app_config import LOGGER_NAME
from utils.config.constants import (
    DEFAULT_FALLBACK_CHAIN,
    EDIT_FALLBACK_CHAIN,
    IMAGE_GENERATION_TIMEOUT,
    IMAGE_EDIT_TIMEOUT,
    MAX_IMAGE_RETRIES
)
from models.image.flux import generate_flux
from models.image.sdxl import generate_sdxl
from models.image.dalle import generate_dalle
from models.image.gptimage import generate_gpt_image
from models.image.imagen import generate_imagen
from models.image.kontext import generate_kontext
from models.image.nanobanana import generate_nanobanana
from models.image.qwenimage import generate_qwen
from models.image.seedream import generate_seedream

logger = logging.getLogger(LOGGER_NAME)

# Model routing table
MODEL_HANDLERS = {
    "flux": generate_flux,
    "sdxl": generate_sdxl,
    "dalle": generate_dalle,
    "dall-e-3": generate_dalle,
    "gpt-image": generate_gpt_image,
    "gpt-image-1": generate_gpt_image,
    "gpt_image": generate_gpt_image,
    "gptimage": generate_gpt_image,
    "imagen": generate_imagen,
    "imagen-3-fast": generate_imagen,
    "kontext": generate_kontext,
    "nanobanana": generate_nanobanana,
    "qwenimage": generate_qwen,
    "qwen": generate_qwen,
    "seedream": generate_seedream,
}


async def generate_image(
    prompt: str,
    model: str = "flux",
    size: str = "1024x1024",
    output_format: Literal["base64", "bytes", "raw"] = "base64",
    use_fallback: bool = True,
    is_edit: bool = False
) -> str | bytes:
    """Generate image from text prompt using specified model.
    
    Supports multiple image generation models with automatic fallback chain.
    
    Args:
        prompt: Text description of image to generate.
        model: Model name (default: 'flux'). Options in MODEL_HANDLERS.
        size: Image dimensions as "WxH" (default: '1024x1024').
        output_format: Return format ('base64' string, 'bytes', or 'raw' model output).
        use_fallback: If True, try fallback models on failure.
        is_edit: If True, use edit-mode fallback chain.
        
    Returns:
        Generated image in requested format (str or bytes).
        
    Raises:
        Exception: If image generation fails with all available models.
        
    Example:
        >>> image_base64 = await generate_image("A sunset over mountains")
        >>> image_bytes = await generate_image("Cat", output_format="bytes")
    """
    logger.info(f"Image generation - model: {model}, size: {size}, format: {output_format}")
    
    # Build model chain
    models_to_try = [model]
    if use_fallback:
        fallback_chain = EDIT_FALLBACK_CHAIN if is_edit else DEFAULT_FALLBACK_CHAIN
        models_to_try.extend([m for m in fallback_chain if m != model])
    
    # Try each model in sequence
    for current_model in models_to_try:
        try:
            logger.debug(f"Attempting generation with {current_model}")
            result = await _generate_with_model(prompt, current_model, size)
            
            if result is not None:
                if current_model != model:
                    logger.info(f"Fallback success with {current_model}")
                else:
                    logger.debug(f"Generation successful with {current_model}")
                
                return _convert_output_format(result, output_format)
            
        except Exception as e:
            logger.debug(f"Model {current_model} failed: {str(e)}")
            if current_model == model:
                logger.warning(f"Primary model {model} failed: {str(e)}")
            continue
    
    logger.error("Image generation failed - all models exhausted")
    raise Exception("Image generation failed with all available models")


async def _generate_with_model(prompt: str, model: str, size: str) -> str | None:
    """Call appropriate image generation model handler.
    
    Args:
        prompt: Image description.
        model: Model identifier key.
        size: Image size specification.
        
    Returns:
        Image as base64 string or None if generation fails.
    """
    model_lower = model.lower()
    
    if model_lower not in MODEL_HANDLERS:
        logger.warning(f"Unknown model: {model}")
        return None
    
    try:
        logger.debug(f"Calling handler for {model_lower}")
        handler = MODEL_HANDLERS[model_lower]
        result = await handler(prompt, size)
        return result
    except Exception as e:
        logger.warning(f"Handler call failed for {model}: {str(e)}")
        raise


def _convert_output_format(image_data: str, format: str) -> str | bytes:
    """Convert image base64 string to requested output format.
    
    Args:
        image_data: Image as base64 string.
        format: Target format ('base64', 'bytes', or 'raw').
        
    Returns:
        Image in requested format.
    """
    if format == "base64":
        return image_data
    elif format == "bytes":
        return base64.b64decode(image_data)
    else:  # "raw"
        return image_data


async def image_edit(
    image_url: str,
    prompt: str,
    model: str = "gpt_image",
    size: str = "1024x1024",
    output_format: Literal["base64", "bytes"] = "base64"
) -> str | bytes:
    """Edit/modify existing image based on text prompt.
    
    Args:
        image_url: URL or path to source image.
        prompt: Description of desired edits/modifications.
        model: Edit-capable model (default: 'gpt_image').
        size: Output size.
        output_format: Return format.
        
    Returns:
        Edited image in requested format.
    """
    logger.info(f"Image edit request - model: {model}, size: {size}")
    return await generate_image(
        prompt,
        model=model,
        size=size,
        output_format=output_format,
        use_fallback=True,
        is_edit=True
    )
