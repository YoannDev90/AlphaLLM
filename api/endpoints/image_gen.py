from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from typing import Optional
import asyncio
from . import logger, REQUEST_TIMEOUT
from api.utils.security_utils import get_api_key

router = APIRouter()

@router.get("/generate/image", tags=["generation"])
async def generate_image(
    prompt: str, 
    model: Optional[str] = "flux", 
    size: Optional[str] = "1024x1024",
    enhance: bool = True,
    api_key: Optional[str] = Depends(get_api_key)
):
    try:
        logger.info(f"Début de génération d'image - Modèle: {model}, Taille: {size}, Enhance: {enhance}")
        logger.debug(f"Prompt reçu: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        
        final_prompt = prompt
        if enhance:
            logger.debug("Amélioration du prompt demandée")
            from utils.ai_utils import enhance_image_prompt
            enhanced_prompts = await enhance_image_prompt(prompt, number=1)
            final_prompt = enhanced_prompts.get(1, prompt)
            logger.info(f"Prompt amélioré: {final_prompt[:100]}{'...' if len(final_prompt) > 100 else ''}")
        
        from utils.image_gen import generate_image
        
        logger.debug(f"Démarrage de la génération avec timeout de {REQUEST_TIMEOUT * 2}s")
        response = await asyncio.wait_for(
            generate_image(prompt=final_prompt, model=model, size=size, output_format="base64"),
            timeout=REQUEST_TIMEOUT * 2
        )
        
        if response is None:
            logger.error("La génération d'image a retourné None")
            return {"status": "error", "message": "Échec de la génération d'image"}
        
        logger.debug(f"Type de réponse reçu: {type(response)}")
        
        return {
            "status": "success", 
            "image_data": response,
            "enhanced_prompt": final_prompt if enhance else None,
            "format": "base64",
            "size_bytes": len(response)
        }
                
    except asyncio.TimeoutError:
        logger.error(f"Timeout lors de la génération de l'image avec le modèle {model}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Timeout lors de la génération de l'image"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'image : {str(e)}")
        return {"status": "error", "message": "Erreur interne lors de la génération d'image"}