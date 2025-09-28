from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from typing import Optional
import asyncio
import base64

from . import logger, REQUEST_TIMEOUT
from api.utils.security_utils import get_api_key

router = APIRouter()

@router.get("/generate/image", tags=["generation"])
async def generate_image(
    model: str, 
    prompt: str, 
    size: str,
    api_key: Optional[str] = Depends(get_api_key)
):
    try:
        from utils.image_gen import generate_image
        
        response = await asyncio.wait_for(
            generate_image(prompt=prompt, model=model, size=size),
            timeout=REQUEST_TIMEOUT * 2
        )
        
        if response is None:
            return {"status": "error", "message": "Échec de la génération d'image"}
        
        if isinstance(response, tuple):
            image_data, is_url = response
            
            if is_url or isinstance(image_data, str):
                return {"status": "success", "image_url": image_data}
            elif isinstance(image_data, bytes):
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                return {
                    "status": "success", 
                    "image_data": image_b64,
                    "format": "base64",
                    "size_bytes": len(image_data)
                }
            else:
                return {"status": "error", "message": "Format d'image non supporté"}
        else:
            if isinstance(response, str):
                return {"status": "success", "image_url": response}
            elif isinstance(response, bytes):
                image_b64 = base64.b64encode(response).decode('utf-8')
                return {
                    "status": "success", 
                    "image_data": image_b64,
                    "format": "base64",
                    "size_bytes": len(response)
                }
            else:
                return {"status": "error", "message": "Type de réponse non supporté"}
                
    except asyncio.TimeoutError:
        logger.error(f"Timeout lors de la génération de l'image avec le modèle {model}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Timeout lors de la génération de l'image"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'image : {str(e)}")
        return {"status": "error", "message": str(e)}