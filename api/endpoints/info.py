from fastapi import APIRouter, Depends, HTTPException, status
import logging
import asyncio
from api.utils.models_utils import load_models_data
from utils.config import LOGGER_NAME
from . import REQUEST_TIMEOUT

logger = logging.getLogger(LOGGER_NAME)
router = APIRouter()

@router.get("/text-models", tags=["info"])
async def get_text_models():
    try:
        logger.info("Requête pour obtenir la liste des modèles de texte")
        text_models = load_models_data("text")
        logger.info(f"Liste des modèles de texte récupérée avec succès - {len(text_models)} modèles disponibles")
        
        return {
            "status": "success",
            "count": len(text_models),
            "models": text_models,
            "default_model": "llama"
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des modèles de texte: {str(e)}")
        return {
            "status": "error",
            "message": "Erreur lors de la récupération des modèles de texte"
        }

@router.get("/image-models", tags=["info"])
async def get_image_models():
    try:
        logger.info("Requête pour obtenir la liste des modèles d'image")
        image_models = load_models_data("image")
        logger.info(f"Liste des modèles d'image récupérée avec succès - {len(image_models)} modèles disponibles")
        
        return {
            "status": "success",
            "count": len(image_models),
            "models": image_models,
            "default_model": "flux"
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des modèles d'image: {str(e)}")
        return {
            "status": "error",
            "message": "Erreur lors de la récupération des modèles d'image"
        }

# @router.get("/voices", tags=["info"])
# async def get_voices():
#     """
#     # Liste des Voix Audio Disponibles
    
#     Récupère toutes les voix disponibles pour la génération audio (TTS) avec leurs caractéristiques.
    
#     ## Informations fournies pour chaque voix:
#     - **ID**: Identifiant unique à utiliser dans les requêtes de génération
#     - **Nom**: Nom convivial de la voix
#     - **Langue**: Code de langue (ex: "en-US", "fr-FR")
#     - **Genre**: "male", "female", ou "neutral"
#     - **Âge**: "adult", "child", "elderly" (si disponible)
#     - **Style**: "natural", "news", "conversational" (si disponible)
    
#     ## Exemple de réponse:
#     ```json
#     {
#         "status": "success",
#         "voices": [
#             {
#                 "id": "oliver",
#                 "name": "Oliver",
#                 "language": "en-US", 
#                 "gender": "male",
#                 "age": "adult",
#                 "style": "natural"
#             },
#             {
#                 "id": "sarah",
#                 "name": "Sarah",
#                 "language": "en-US",
#                 "gender": "female", 
#                 "age": "adult",
#                 "style": "conversational"
#             }
#         ]
#     }
#     ```
    
#     ## Utilisation:
#     1. Appeler cet endpoint pour découvrir les voix disponibles
#     2. Choisir une voix selon vos critères (langue, genre, style)
#     3. Utiliser l'ID de la voix dans les endpoints de génération audio
    
#     **Note**: Cet endpoint est public et ne nécessite pas d'authentification.
#     """
#     try:
#         logger.info("Requête API reçue - Liste des voix")
        
#         # Import dynamique pour éviter les dépendances circulaires
#         from utils.audio_gen import list_voices
        
#         async def get_voices_list():
#             voices = await list_voices()
#             logger.info(f"Nombre de voix disponibles: {len(voices) if voices else 0}")
#             return voices
        
#         voices = await asyncio.wait_for(
#             get_voices_list(),
#             timeout=REQUEST_TIMEOUT
#         )
        
#         if not voices:
#             logger.warning("Aucune voix disponible")
#             return {"status": "success", "voices": [], "message": "Aucune voix disponible"}
        
#         return {"status": "success", "voices": voices}
        
#     except asyncio.TimeoutError:
#         logger.error("Timeout lors de la récupération des voix")
#         raise HTTPException(
#             status_code=status.HTTP_408_REQUEST_TIMEOUT,
#             detail="Timeout lors de la récupération des voix"
#         )
#     except Exception as e:
#         logger.error(f"Erreur lors de la récupération des voix : {str(e)}")
#         return {"status": "error", "message": "Une erreur interne s'est produite lors de la récupération des voix."}

@router.get("/api/info", tags=["info"])
async def api_info():
    try:
        logger.info("Requête pour obtenir les informations de l'API")
        from utils.config import API_KEY_REQUIRED, MAX_REQUESTS_PER_MINUTE, REQUEST_TIMEOUT
        
        logger.debug(f"Configuration API: AUTH_REQUIRED={API_KEY_REQUIRED}, RATE_LIMIT={MAX_REQUESTS_PER_MINUTE}, TIMEOUT={REQUEST_TIMEOUT}")
        
        return {
            "api_version": "1.0.0",
            "authentication_required": API_KEY_REQUIRED,
            "rate_limit": {
                "max_requests_per_minute": MAX_REQUESTS_PER_MINUTE,
                "window_seconds": 60
            },
            "timeout_seconds": REQUEST_TIMEOUT,
            "authenticated": False,
            "endpoints": {
                "/": "Point d'entrée principal",
                "/status": "Statut de l'API",
                "/generate/text": "Génération de texte (authentification requise)",
                "/generate/image": "Génération d'image (authentification requise)",
                "/generate/audio": "Génération audio MP3 (authentification requise)",
                "/summarize": "Résumé automatique de texte (authentification requise)",
                "/conv_name": "Génération de titre de conversation (authentification requise)",
                "/text-models": "Liste des modèles de texte disponibles (public)",
                "/image-models": "Liste des modèles d'image disponibles (public)",
                "/voices": "Liste des voix audio disponibles (public)",
                "/api/info": "Informations sur l'API (public)",
                "/docs": "Documentation Swagger",
                "/redoc": "Documentation ReDoc"
            },
            "authentication_methods": [
                "Header: Authorization: Bearer <api_key>",
                "Header: X-API-Key: <api_key>",
                "Query parameter: ?api_key=<api_key>"
            ]
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations de l'API: {str(e)}")
        return {
            "status": "error",
            "message": "Erreur lors de la récupération des informations de l'API"
        }