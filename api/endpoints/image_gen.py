from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from typing import Optional
import asyncio
from . import logger, REQUEST_TIMEOUT
from api.utils.security_utils import get_api_key

router = APIRouter()

@router.get("/generate/image", 
           tags=["generation"],
           summary="Générer une image",
           description="Génère une image à partir d'un prompt en utilisant différents modèles d'IA",
           response_description="Image générée avec métadonnées")
async def generate_image(
    prompt: str = Query(..., description="Prompt pour générer l'image", min_length=1, max_length=2000),
    model: Optional[str] = Query("flux", description="Modèle d'IA à utiliser (flux, dalle, kontext, turbo, seedream, nanobanana, etc.)"),
    size: Optional[str] = Query("1024x1024", description="Taille de l'image (format: largeurxhauteur, ex: 1024x1024, 512x512)"),
    format: Optional[str] = Query("base64", description="Format de sortie de l'image", regex="^(base64|bytes|raw)$"),
    enhance: bool = Query(True, description="Améliorer automatiquement le prompt avec l'IA"),
    api_key: Optional[str] = Depends(get_api_key)
):
    try:
        # Validation du format
        valid_formats = ["base64", "bytes", "raw"]
        if format.lower() not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Format invalide. Formats supportés: {', '.join(valid_formats)}"
            )
        
        logger.info(f"Début de génération d'image - Modèle: {model}, Taille: {size}, Format: {format}, Enhance: {enhance}")
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
            generate_image(prompt=final_prompt, model=model, size=size, output_format=format),
            timeout=REQUEST_TIMEOUT * 2
        )
        
        if response is None:
            logger.error("La génération d'image a retourné None")
            return {"status": "error", "message": "Échec de la génération d'image"}
        
        logger.debug(f"Type de réponse reçu: {type(response)}")
        
        # Calcul de la taille selon le format
        if format == "bytes":
            size_info = len(response) if response else 0
            content_type = "bytes"
        elif format == "base64":
            size_info = len(response) if response else 0
            content_type = "string"
        else:  # raw
            size_info = len(str(response)) if response else 0
            content_type = "string"
        
        return {
            "status": "success", 
            "image_data": response,
            "enhanced_prompt": final_prompt if enhance else None,
            "format": format,
            "content_type": content_type,
            "size_info": size_info
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