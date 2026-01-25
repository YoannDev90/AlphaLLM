import base64
import json
import logging
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, List, Optional, Union

import aiohttp

from config import LOGGER_NAME
from models.image.flux import generate_flux
from models.image.gptimage import generate_gptimage
from models.image.kontext import generate_kontext
from models.image.nanobanana import generate_nanobanana
from models.image.seedream import generate_seedream
from models.image.zimage import generate_zimage
from utils.ai_process.ai_utils import enhance_image_prompt
from utils.handlers.images import (auto_enhance_image, enhance_image,
                                   generative_restore, improve_image,
                                   remove_background, upload_images,
                                   upscale_image)

logger = logging.getLogger(LOGGER_NAME)

class Image_Model(Enum):
    """Enum pour définir les modèles disponibles."""
    FLUX = "flux"
    GPT_IMAGE = "gptimage"
    KONTEXT = "kontext"
    NANOBANANA = "nanobanana"
    SEEDREAM = "seedream"
    ZIMAGE = "zimage"

class Format(Enum):
    """Enum pour définir les formats d'image."""
    URL = "url"
    BASE64 = "base64"
    BYTES = "bytes"

class Transformation_Type(Enum):
    """Enum pour définir les types de transformation d'image."""
    REMOVE_BG = "remove_bg"
    ENHANCE = "enhance"
    UPSCALE = "upscale"
    GENERATIVE_RESTORE = "generative_restore"
    IMPROVE = "improve"
    AUTO_ENHANCE = "auto_enhance"

FALLBACK_ORDER = [
    Image_Model.FLUX.value,
    Image_Model.ZIMAGE.value,
    Image_Model.GPT_IMAGE.value,
    Image_Model.SEEDREAM.value,
    Image_Model.NANOBANANA.value,
    Image_Model.KONTEXT.value,
]

EDIT_FALLBACK_ORDER = [
    Image_Model.GPT_IMAGE.value,
    Image_Model.KONTEXT.value,
    Image_Model.SEEDREAM.value,
    Image_Model.NANOBANANA.value,
]

IMAGE_GEN_FUNCTIONS = {
    Image_Model.FLUX.value: generate_flux,
    Image_Model.GPT_IMAGE.value: generate_gptimage,
    Image_Model.KONTEXT.value: generate_kontext,
    Image_Model.NANOBANANA.value: generate_nanobanana,
    Image_Model.SEEDREAM.value: generate_seedream,
    Image_Model.ZIMAGE.value: generate_zimage,
}

IMAGE_EDIT_FUNCTIONS = {
    Image_Model.GPT_IMAGE.value: generate_gptimage,
    Image_Model.KONTEXT.value: generate_kontext,
    Image_Model.NANOBANANA.value: generate_nanobanana,
    Image_Model.SEEDREAM.value: generate_seedream,
}

IMAGE_TRANSFORMATION_FUNCTIONS = {
    Transformation_Type.REMOVE_BG.value: remove_background,
    Transformation_Type.ENHANCE.value: enhance_image,
    Transformation_Type.UPSCALE.value: upscale_image,
    Transformation_Type.GENERATIVE_RESTORE.value: generative_restore,
    Transformation_Type.IMPROVE.value: improve_image,
    Transformation_Type.AUTO_ENHANCE.value: auto_enhance_image,
}

async def convert_format(image_data: str, target_format: Format) -> Union[str, BytesIO]:
    """Convertit les données d'image au format souhaité."""
    if target_format == Format.BASE64:
        return image_data
    elif target_format == Format.BYTES:
        image_bytes = base64.b64decode(image_data)
        return BytesIO(image_bytes)
    else:
        raise ValueError(f"Unsupported format: {target_format}")
    
def validate_image_size(model: str, size: str) -> bool:
    """Renvoie la taille d'origine si valide, et la taille la plus proche d'un point de vue du ratio sinon"""
    models_info = json.loads(open(Path("api/models/image_models.json"), "r").read())
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
    
##############################################################################################

async def unified_image_gen(
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
        enhanced_dict = await enhance_image_prompt(prompt, num_images, is_edit=False)
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

async def _generate_with_fallbacks(prompt: str, size: str, primary_model: str) -> Optional[str]:
    """Tente de générer une image avec le modèle primaire, puis les fallbacks."""
    models_to_try = [primary_model] + FALLBACK_ORDER
    
    for model in models_to_try:
        if model in IMAGE_GEN_FUNCTIONS:
            try:
                logger.debug(f"Trying model: {model}")
                result = await IMAGE_GEN_FUNCTIONS[model](prompt, size)
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

##############################################################################################

async def unified_image_edit(
        prompt: str,
        model: Union[str, Image_Model],
        num_images: int = 1,
        enhance: bool = True,
        format: Union[str, Format] = Format.BASE64,
        images_url: List[str] = [],
        user_id: int = None,
    ) -> list[tuple[Union[str, BytesIO], str]]:
    """Gère l'édition d'images en fonction du modèle spécifié."""

    model = model or Image_Model.GPT_IMAGE.value
    num_images = min(max(1, num_images), 4)
    file_bytes = BytesIO(await (await aiohttp.ClientSession().get(images_url[0])).read())
    size = get_size(file_bytes)
    images_url = await upload_images(images_url)

    if enhance:
        enhanced_dict = await enhance_image_prompt(prompt, num_images, is_edit=True)
        prompts = list(enhanced_dict.values())
    else : 
        prompts = [prompt] * num_images

    results = []
    for p in prompts:
        logger.debug(f"Using prompt: {p}")
        img_b64 = await _edit_with_fallbacks(p, size, images_url, model.lower())
        if img_b64 is not None:
            result = await convert_format(img_b64, Format(format))
            results.append((result, p))
        else:
            results.append((None, p))
    
    return results

async def _edit_with_fallbacks(prompt: str, size: str, images_url: list[str], primary_model: str) -> Optional[str]:
    """Tente de générer une image avec le modèle primaire, puis les fallbacks."""
    models_to_try = [primary_model] + EDIT_FALLBACK_ORDER
    
    for model in models_to_try:
        if model in IMAGE_EDIT_FUNCTIONS:
            try:
                logger.debug(f"Trying model: {model}")
                result = await IMAGE_EDIT_FUNCTIONS[model](prompt, size, images_url)
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

def get_size(file_bytes: BytesIO) -> str:
    """Renvoie les dimensions (width, height) d'une image à partir de ses bytes."""
    from PIL import Image
    file_bytes.seek(0)
    with Image.open(file_bytes) as img:
        width, height = img.size
        return f"{width}x{height}"

##############################################################################################

async def unified_image_transform(
        transformations: List[str],
        format: Union[str, Format] = Format.BASE64,
        image_url: str = "",
        user_id: int = None,
    ) -> list[tuple[Union[str, BytesIO], str]]:
    """Gère les transformations d'une image spécifiée."""

    image_url = await upload_images([image_url])
    image_url = image_url[0]

    logger.info(f"Applying transformations {', '.join(transformations)} to image.")
    for trans in transformations:
        match trans:
            case Transformation_Type.REMOVE_BG.value | "remove_bg":
                image_url = remove_background(image_url)
            case Transformation_Type.ENHANCE.value | "enhance":
                image_url = enhance_image(image_url)
            case Transformation_Type.UPSCALE.value | "upscale":
                image_url = upscale_image(image_url)
            case Transformation_Type.GENERATIVE_RESTORE.value | "generative_restore":
                image_url = generative_restore(image_url)
            case Transformation_Type.IMPROVE.value | "improve":
                image_url = improve_image(image_url)
            case Transformation_Type.AUTO_ENHANCE.value | "auto_enhance":
                image_url = auto_enhance_image(image_url)
            case _:
                logger.warning(f"Unknown transformation: {trans}, skipping.")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    b64 = base64.b64encode(image_bytes).decode('utf-8')
                    return await convert_format(b64, Format(format))
                else:
                    logger.error(f"Failed to download transformed image: {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"Error downloading transformed image: {e}")
        return None




