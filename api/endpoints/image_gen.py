from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from typing import Optional
import asyncio
import base64
import json
import os

from . import logger, REQUEST_TIMEOUT
from api.utils.security_utils import get_api_key

router = APIRouter()

@router.get("/generate/image", tags=["generation"])
async def generate_image(
    model: Optional[str], 
    prompt: str, 
    size: Optional[str],
    api_key: Optional[str] = Depends(get_api_key)
):
    try:
        logger.info(f"Début de génération d'image - Modèle: {model}, Taille: {size}")
        logger.debug(f"Prompt reçu: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        
        from utils.image_gen import generate_image
        
        logger.debug(f"Démarrage de la génération avec timeout de {REQUEST_TIMEOUT * 2}s")
        response = await asyncio.wait_for(
            generate_image(prompt=prompt, model=model, size=size),
            timeout=REQUEST_TIMEOUT * 2
        )
        
        if response is None:
            logger.error("La génération d'image a retourné None")
            return {"status": "error", "message": "Échec de la génération d'image"}
        
        logger.debug(f"Type de réponse reçu: {type(response)}")
        
        if isinstance(response, tuple):
            image_data, is_url = response
            logger.debug(f"Réponse tuple - Type de données: {type(image_data)}, Est une URL: {is_url}")
            
            if is_url or isinstance(image_data, str):
                logger.info(f"Image générée avec succès - URL: {image_data[:50]}{'...' if len(str(image_data)) > 50 else ''}")
                return {"status": "success", "image_url": image_data}
            elif isinstance(image_data, bytes):
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                logger.info(f"Image générée avec succès - Données binaires encodées en base64 ({len(image_data)} bytes)")
                return {
                    "status": "success", 
                    "image_data": image_b64,
                    "format": "base64",
                    "size_bytes": len(image_data)
                }
            else:
                logger.error(f"Format d'image non supporté dans tuple: {type(image_data)}")
                return {"status": "error", "message": "Format d'image non supporté"}
        else:
            if isinstance(response, bytes):
                image_b64 = base64.b64encode(response).decode('utf-8')
                logger.info(f"Image générée avec succès")
                return {
                    "status": "success", 
                    "image_data": image_b64,
                    "format": "base64",
                    "size_bytes": len(response)
                }
            else:
                logger.error(f"Type de réponse non supporté: {type(response)}")
                return {"status": "error", "message": "Type de réponse non supporté"}
                
    except asyncio.TimeoutError:
        logger.error(f"Timeout lors de la génération de l'image avec le modèle {model}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Timeout lors de la génération de l'image"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'image : {str(e)}")
        return {"status": "error", "message": "Erreur interne lors de la génération d'image"}