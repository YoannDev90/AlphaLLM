import base64
import logging
import os
from typing import List, Optional, Union

import aiohttp
import cloudinary
import cloudinary.uploader
import requests

from config import CLOUDINARY_URL, IMGBB_API_KEY, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
cloudinary.config(cloud_url=CLOUDINARY_URL)

async def upload_images(images: List[Union[str, bytes]]) -> List[str]:
    """
    Upload des images sur imgbb avec une expiration de 24 heures.

    Args:
        images: Liste des chemins de fichiers, URLs, données binaires ou base64 des images.
    Returns:
        Liste des URLs des images uploadées, ou None en cas d'erreur.
    """
    urls = []
    expiration_seconds = 24 * 60 * 60
    async with aiohttp.ClientSession() as session:
        for img in images:
            try:
                if isinstance(img, bytes):
                    img_data = img
                elif isinstance(img, str):
                    if img.startswith(('http://', 'https://')):
                        # URL
                        async with session.get(img) as resp:
                            if resp.status == 200:
                                img_data = await resp.read()
                            else:
                                logger.error(f"Failed to download image from {img}: {resp.status}")
                                urls.append(None)
                                continue
                    else:
                        # Assume base64 string
                        try:
                            img_data = base64.b64decode(img)
                        except Exception:
                            # Assume file path
                            with open(img, 'rb') as f:
                                img_data = f.read()
                else:
                    img_data = img  # bytes

                img_b64 = base64.b64encode(img_data).decode('utf-8')

                data = {
                    'key': IMGBB_API_KEY,
                    'image': img_b64,
                    'expiration': expiration_seconds
                }

                response = requests.post('https://api.imgbb.com/1/upload', data=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        urls.append(result['data']['url'])
                    else:
                        urls.append(None)
                else:
                    urls.append(None)

            except Exception as e:
                logger.error(f"Erreur lors de l'upload d'une image: {e}")
                urls.append(None)

    return urls

def remove_background(image_url: str) -> str:
    """
    Supprime l'arrière-plan d'une image en utilisant Cloudinary.

    Args:
        image_url: URL de l'image source.

    Returns:
        URL de l'image transformée.
    """
    try:
        upload_result = cloudinary.uploader.upload(image_url)
        public_id = upload_result['public_id']
        transformed_url, options = cloudinary.utils.cloudinary_url(
            public_id,
            transformation=[{'effect': 'bgremoval'}]
        )
        return transformed_url
    except Exception as e:
        logger.error(f"Error during remove_background: {e}")
        return image_url
    
def upscale_image(image_url: str) -> str:
    """
    Améliore la résolution de l'image en utilisant la super résolution de Cloudinary.

    Args:
        image_url: URL de l'image source.

    Returns:
        URL de l'image transformée.
    """
    try:
        upload_result = cloudinary.uploader.upload(image_url)
        public_id = upload_result['public_id']
        transformed_url, options = cloudinary.utils.cloudinary_url(
            public_id,
            transformation=[{'effect': 'upscale'}]
        )
        return transformed_url
    except Exception as e:
        logger.error(f"Error during upscale_image: {e}")
        return image_url

def enhance_image(image_url: str) -> str:
    """
    Améliore la qualité de l'image en utilisant Cloudinary.

    Args:
        image_url: URL de l'image source.

    Returns:
        URL de l'image transformée.
    """
    try:
        upload_result = cloudinary.uploader.upload(image_url)
        public_id = upload_result['public_id']
        transformed_url, options = cloudinary.utils.cloudinary_url(
            public_id,
            transformation=[{'effect': 'enhance'}]
        )
        return transformed_url
    except Exception as e:
        logger.error(f"Error during enhance_image: {e}")
        return image_url

def generative_restore(image_url: str) -> str:
    """
    Restaure une image affectée par la manipulation numérique et la compression en utilisant Cloudinary.

    Args:
        image_url: URL de l'image source.

    Returns:
        URL de l'image transformée.
    """
    try:
        upload_result = cloudinary.uploader.upload(image_url)
        public_id = upload_result['public_id']
        transformed_url, options = cloudinary.utils.cloudinary_url(
            public_id,
            transformation=[{'effect': 'gen_restore'}]
        )
        return transformed_url
    except Exception as e:
        logger.error(f"Error during generative_restore: {e}")
        return image_url

def improve_image(image_url: str) -> str:
    """
    Améliore automatiquement les images en ajustant les couleurs, le contraste et l'éclairage en utilisant Cloudinary.

    Args:
        image_url: URL de l'image source.

    Returns:
        URL de l'image transformée.
    """
    try:
        upload_result = cloudinary.uploader.upload(image_url)
        public_id = upload_result['public_id']
        transformed_url, options = cloudinary.utils.cloudinary_url(
            public_id,
            transformation=[{'effect': 'improve'}]
        )
        return transformed_url
    except Exception as e:
        logger.error(f"Error during improve_image: {e}")
        return image_url

def auto_enhance_image(image_url: str) -> str:
    """
    Améliore automatiquement la qualité visuelle globale sans choisir l'option d'amélioration en utilisant Cloudinary.

    Args:
        image_url: URL de l'image source.

    Returns:
        URL de l'image transformée.
    """
    try:
        upload_result = cloudinary.uploader.upload(image_url)
        public_id = upload_result['public_id']
        transformed_url, options = cloudinary.utils.cloudinary_url(
            public_id,
            transformation=[{'effect': 'auto_enhance'}]
        )
        return transformed_url
    except Exception as e:
        logger.error(f"Error during auto_enhance_image: {e}")
        return image_url

