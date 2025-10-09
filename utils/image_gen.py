import logging
from utils.config import LOGGER_NAME

# Imports des modèles d'image
from models.image.flux import generate_flux
from models.image.flux_schnell import generate_flux_schnell
from models.image.sdxl import generate_sdxl
from models.image.sdlarge import generate_sdlarge
from models.image.dalle import generate_dalle
from models.image.gpt_image import generate_gpt_image
from models.image.imagen import generate_imagen
from models.image.recraft import generate_recraft
from models.image.sana import generate_sana
from models.image.playground import generate_playground
from models.image.phoenix import generate_phoenix
from models.image.kontext import generate_kontext
from models.image.nanobanana import generate_nanobanana
from models.image.seedream import generate_seedream
from models.image.turbo import generate_turbo

logger = logging.getLogger(LOGGER_NAME)

async def generate_image(prompt: str, model: str = None, size: str = "1024x1024", output_format: str = "base64", use_fallback: bool = True, is_edit: bool = False):
    """
    Génère une image avec le modèle spécifié
    
    Args:
        prompt: Le prompt pour générer l'image
        model: Le modèle à utiliser (par défaut: flux)
        size: La taille de l'image (par défaut "1024x1024")
        output_format: Format de sortie ("base64", "bytes", "raw")
        use_fallback: Si True, essaie d'autres modèles en cas d'échec (défaut: True)
        
    Returns:
        L'image dans le format demandé:
        - "base64": string base64 (défaut)
        - "bytes": données binaires (bytes)
        - "raw": retour direct du modèle
    """
    import base64
    
    model = "flux" if model is None else model
    if is_edit:
        fallback_models = ["gpt_image", "imagen", "kontext", "nanobanana"]
    else:
        fallback_models = ["flux", "sdxl", "turbo", "dalle", "flux_schnell", "sdlarge", "gpt_image", "imagen", "recraft", "sana", "playground", "phoenix", "kontext", "nanobanana", "seedream"]

    models_to_try = [model]
    if use_fallback:
        for fallback in fallback_models:
            models_to_try.append(fallback) if fallback != model else None
    
    logger.info(f"Génération d'image avec le modèle: {model}, format: {output_format}")
    
    for current_model in models_to_try:
        try:
            logger.debug(f"Tentative avec le modèle: {current_model}")
            result = await _generate_with_model(prompt, current_model, size)
            
            if result is not None:
                if current_model != model:
                    logger.info(f"Génération réussie avec le modèle de fallback: {current_model}")
                else:
                    logger.info(f"Génération réussie avec le modèle demandé: {current_model}")
                
                return _convert_output_format(result, output_format)
            
        except Exception as e:
            logger.warning(f"Échec avec le modèle {current_model}: {str(e)}")
            if current_model == model:
                logger.error(f"Erreur avec le modèle principal {model}: {str(e)}")
            continue
    
    logger.error("Tous les modèles ont échoué pour la génération d'image")
    raise Exception("Échec de la génération d'image avec tous les modèles disponibles")

async def _generate_with_model(prompt: str, model: str, size: str):
    """
    Fonction interne pour générer une image avec un modèle spécifique
    
    Returns:
        L'image en base64 ou None si échec
    """
    try:
        result = None
        match model.lower():
            case "flux":
                logger.debug("Utilisation du modèle Flux")
                result = await generate_flux(prompt, size)
            
            case "flux-schnell" | "flux_schnell":
                logger.debug("Utilisation du modèle Flux Schnell")
                result = await generate_flux_schnell(prompt, size)
            
            case "sdxl":
                logger.debug("Utilisation du modèle Stable Diffusion XL")
                result = await generate_sdxl(prompt, size)
            
            case "sd3.5-large" | "sdlarge":
                logger.debug("Utilisation du modèle Stable Diffusion 3.5 Large")
                result = await generate_sdlarge(prompt, size)
            
            case "dalle" | "dall-e-3":
                logger.debug("Utilisation du modèle DALL-E 3")
                result = await generate_dalle(prompt, size)
            
            case "gpt-image" | "gpt-image-1" | "gpt_image":
                logger.debug("Utilisation du modèle GPT-Image-1")
                result = await generate_gpt_image(prompt, size)
            
            case "imagen" | "imagen-3-fast":
                logger.debug("Utilisation du modèle Imagen 3 Fast")
                result = await generate_imagen(prompt, size)
            
            case "recraft" | "recraft-20b":
                logger.debug("Utilisation du modèle Recraft 20B")
                result = await generate_recraft(prompt, size)
            
            case "sana":
                logger.debug("Utilisation du modèle Sana")
                result = await generate_sana(prompt, size)
            
            case "playground" | "playground-v2.5":
                logger.debug("Utilisation du modèle Playground v2.5")
                result = await generate_playground(prompt, size)
            
            case "phoenix" | "phoenix-1.0":
                logger.debug("Utilisation du modèle Phoenix 1.0")
                result = await generate_phoenix(prompt, size)
            
            case "kontext":
                logger.debug("Utilisation du modèle Kontext")
                result = await generate_kontext(prompt, size)
            
            case "nanobanana":
                logger.debug("Utilisation du modèle Nanobanana")
                result = await generate_nanobanana(prompt, size)
            
            case "seedream":
                logger.debug("Utilisation du modèle Seedream")
                result = await generate_seedream(prompt, size)
            
            case "turbo":
                logger.debug("Utilisation du modèle Turbo")
                result = await generate_turbo(prompt, size)
            
            case _:
                logger.warning(f"Modèle inconnu: {model}, utilisation du modèle par défaut (Flux)")
                result = await generate_flux(prompt, size)
        
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération avec le modèle {model}: {str(e)}")
        raise

def _convert_output_format(result: str, output_format: str):
    """
    Convertit le résultat base64 selon le format demandé
    
    Args:
        result: Image en base64
        output_format: Format de sortie demandé
        
    Returns:
        L'image dans le format demandé
    """
    import base64
    
    if result is None:
        return None
        
    match output_format.lower():
        case "base64":
            return result
        case "bytes":
            return base64.b64decode(result)
        case "raw":
            return result
        case _:
            logger.warning(f"Format de sortie inconnu: {output_format}, utilisation de base64")
            return result

async def image_edit(edit_prompt: str, image_url: str, size: str = "1024x1024", output_format: str = "bytes"):
    """
    Édite une image existante avec un nouveau prompt
    
    Args:
        edit_prompt: Le prompt pour éditer l'image
        image_url: L'URL de l'image à éditer
        size: La taille de l'image (par défaut "1024x1024")
        output_format: Format de sortie ("base64", "bytes", "raw")
        
    Returns:
        Tuple (image_data, nsfw_detected)
    """
    try:
        logger.info(f"Édition d'image avec prompt: {edit_prompt}")

        result = await generate_image(edit_prompt, "nanobanana", size, output_format, use_fallback=True)
        
        if result is not None:
            logger.info(f"Édition d'image réussie")
            # NSFW detection placeholder - à implémenter selon vos besoins
            nsfw_detected = False
            return result, nsfw_detected
        else:
            logger.error("Échec de l'édition d'image")
            return None, False
        
    except Exception as e:
        logger.error(f"Erreur lors de l'édition de l'image: {str(e)}")
        return None, False