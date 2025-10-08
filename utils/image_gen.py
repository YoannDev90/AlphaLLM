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

async def generate_image(prompt: str, model: str = None, size: str = "1024x1024") -> str:
    """
    Génère une image avec le modèle spécifié
    
    Args:
        prompt: Le prompt pour générer l'image
        model: Le modèle à utiliser (par défaut: flux)
        size: La taille de l'image (par défaut "1024x1024")
        
    Returns:
        L'image encodée en base64
    """
    try:
        # Modèle par défaut
        if model is None:
            model = "flux"
        
        logger.info(f"Génération d'image avec le modèle: {model}")
        
        match model.lower():
            case "flux":
                logger.debug("Utilisation du modèle Flux")
                return await generate_flux(prompt, size)
            
            case "flux-schnell":
                logger.debug("Utilisation du modèle Flux Schnell")
                return await generate_flux_schnell(prompt, size)
            
            case "sdxl":
                logger.debug("Utilisation du modèle Stable Diffusion XL")
                return await generate_sdxl(prompt, size)
            
            case "sd3.5-large" | "sdlarge":
                logger.debug("Utilisation du modèle Stable Diffusion 3.5 Large")
                return await generate_sdlarge(prompt, size)
            
            case "dalle" | "dall-e-3":
                logger.debug("Utilisation du modèle DALL-E 3")
                return await generate_dalle(prompt, size)
            
            case "gpt-image" | "gpt-image-1":
                logger.debug("Utilisation du modèle GPT-Image-1")
                return await generate_gpt_image(prompt, size)
            
            case "imagen" | "imagen-3-fast":
                logger.debug("Utilisation du modèle Imagen 3 Fast")
                return await generate_imagen(prompt, size)
            
            case "recraft" | "recraft-20b":
                logger.debug("Utilisation du modèle Recraft 20B")
                return await generate_recraft(prompt, size)
            
            case "sana":
                logger.debug("Utilisation du modèle Sana")
                return await generate_sana(prompt, size)
            
            case "playground" | "playground-v2.5":
                logger.debug("Utilisation du modèle Playground v2.5")
                return await generate_playground(prompt, size)
            
            case "phoenix" | "phoenix-1.0":
                logger.debug("Utilisation du modèle Phoenix 1.0")
                return await generate_phoenix(prompt, size)
            
            case "kontext":
                logger.debug("Utilisation du modèle Kontext")
                return await generate_kontext(prompt, size)
            
            case "nanobanana":
                logger.debug("Utilisation du modèle Nanobanana")
                return await generate_nanobanana(prompt, size)
            
            case "seedream":
                logger.debug("Utilisation du modèle Seedream")
                return await generate_seedream(prompt, size)
            
            case "turbo":
                logger.debug("Utilisation du modèle Turbo")
                return await generate_turbo(prompt, size)
            
            case _:
                logger.warning(f"Modèle inconnu: {model}, utilisation du modèle par défaut (Flux)")
                return await generate_flux(prompt, size)
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'image: {str(e)}")
        raise