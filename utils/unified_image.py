import base64
import json
import logging
from enum import Enum
from io import BytesIO
from typing import Any, List, Optional, Union

from config import LOGGER_NAME
from models.image.dalle import generate_dalle
from models.image.flux import generate_flux
from models.image.gptimage import generate_gptimage
from models.image.imagen import generate_imagen
from models.image.kontext import generate_kontext
from models.image.nanobanana import generate_nanobanana
from models.image.seedream import generate_seedream
from models.image.zimage import generate_zimage
from utils.ai_process.ai_utils import enhance_image_prompt

logger = logging.getLogger(LOGGER_NAME)

class Image_Model(Enum):
    """Enum pour définir les modèles disponibles."""
    DALLE = "dalle"
    FLUX = "flux"
    GPT_IMAGE = "gptimage"
    GROK_IMAGE = "grokimage"
    IMAGEN = "imagen"
    KONTEXT = "kontext"
    NANOBANANA = "nanobanana"
    SDXL = "sdxl"
    SEEDREAM = "seedream"
    ZIMAGE = "zimage"

class Format(Enum):
    """Enum pour définir les formats d'image."""
    URL = "url"
    BASE64 = "base64"
    BYTES = "bytes"

FALLBACK_ORDER = [
    Image_Model.FLUX.value,
    Image_Model.ZIMAGE.value,
    Image_Model.GPT_IMAGE.value,
    Image_Model.IMAGEN.value,
    Image_Model.SEEDREAM.value,
    Image_Model.NANOBANANA.value,
    Image_Model.KONTEXT.value,
]

MODEL_FUNCTIONS = {
    Image_Model.DALLE.value: generate_dalle,
    Image_Model.FLUX.value: generate_flux,
    Image_Model.GPT_IMAGE.value: generate_gptimage,
    Image_Model.IMAGEN.value: generate_imagen,
    Image_Model.KONTEXT.value: generate_kontext,
    Image_Model.NANOBANANA.value: generate_nanobanana,
    Image_Model.SEEDREAM.value: generate_seedream,
    Image_Model.ZIMAGE.value: generate_zimage,
}

async def unified_image_manager(
        prompt: str,
        model: Union[str, Image_Model],
        num_images: int = 1,
        size: str = "1024x1024",
        enhance: bool = True,
        format: Union[str, Format] = Format.BASE64,
        user_id: int = None,
    ) -> list[tuple[Union[str, BytesIO], str]]:
    """Gère la génération d'images en fonction du modèle spécifié."""
    model = model or Image_Model.FLUX.value
    num_images = min(max(1, num_images), 4)
    if enhance:
        enhanced_dict = await enhance_image_prompt(prompt, num_images)
        prompts = list(enhanced_dict.values())
    else : 
        prompts = [prompt] * num_images

    size = validate_image_size(model.lower(), size)

    results = []
    for p in prompts:
        logger.debug(f"Using prompt: {p}")
        img_b64 = await _generate_with_fallbacks(p, size, model.lower())
        if img_b64 is not None:
            result = await convert_format(img_b64, Format(format))
            results.append((result, p))
        else:
            results.append((None, p))
    
    return results

def validate_image_size(model: str, size: str) -> bool:
    """Renvoie la taille d'origine si valide, et la taille la plus proche d'un point de vue du ratio sinon"""
    models_info = json.loads(open("api/models/image_models.json", "r").read())
    sizes = models_info[model.lower()].get("supported_sizes", [])
    if size in sizes:
        return size
    else:
        logger.warning(f"Requested size {size} not supported by model {model}. Supported sizes: {sizes}")
        req_width, req_height = map(int, size.split('x'))
        req_ratio = req_width / req_height
        closest_size = None
        closest_diff = float('inf')
        for s in sizes:
            width, height = map(int, s.split('x'))
            ratio = width / height
            diff = abs(req_ratio - ratio)
            if diff < closest_diff:
                closest_diff = diff
                closest_size = s
        logger.info(f"Closest supported size for {size} is {closest_size}")
        return closest_size

async def _generate_with_fallbacks(prompt: str, size: str, primary_model: str) -> Optional[str]:
    """Tente de générer une image avec le modèle primaire, puis les fallbacks."""
    models_to_try = [primary_model] + FALLBACK_ORDER
    
    for model in models_to_try:
        if model in MODEL_FUNCTIONS:
            try:
                logger.debug(f"Trying model: {model}")
                result = await MODEL_FUNCTIONS[model](prompt, size)
                if result is not None:
                    logger.info(f"Successfully generated image with model: {model}")
                    return result
                else:
                    logger.warning(f"Model {model} returned None, trying next fallback.")
            except Exception as e:
                logger.error(f"Error with model {model}: {e}, trying next fallback.")
        else:
            logger.warning(f"Model {model} not found in functions.")
    
    logger.error("All models failed to generate image.")
    return None

async def convert_format(image_data: str, target_format: Format) -> Union[str, BytesIO]:
    """Convertit les données d'image au format souhaité."""
    if target_format == Format.BASE64:
        return image_data
    elif target_format == Format.BYTES:
        image_bytes = base64.b64decode(image_data)
        return BytesIO(image_bytes)
    else:
        raise ValueError(f"Unsupported format: {target_format}")
