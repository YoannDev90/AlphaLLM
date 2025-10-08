# from fastapi import APIRouter, Depends, HTTPException, status
# from typing import Optional
# import asyncio
# import base64

# from . import logger, REQUEST_TIMEOUT
# from api.utils.security_utils import get_api_key
# from utils.audio_gen import generate_speech

# router = APIRouter()

# @router.post("/generate/audio", tags=["generation"])
# async def generate_audio(
#     text: str,
#     voice: str = "oliver",
#     api_key: Optional[str] = Depends(get_api_key)
# ):
#     """
#     # Génération Audio à partir de Texte (TTS)
    
#     Convertit un texte en fichier audio MP3 synthétisé avec une voix naturelle.
    
#     ## Paramètres:
#     - **text**: Le texte à convertir en audio (max 5000 caractères)
#     - **voice**: ID de la voix à utiliser (voir `/voices` pour la liste)
    
#     ## Format de sortie:
#     - **MP3**: Format universel, compatible avec tous les navigateurs et applications
    
#     ## Exemple de réponse:
#     ```json
#     {
#         "status": "success",
#         "audio_data": "base64_encoded_mp3_content",
#         "format": "mp3"
#     }
#     ```
    
#     ## Utilisation:
#     1. Récupérer les voix disponibles avec `/voices`
#     2. Faire la requête avec le texte et la voix choisie
#     3. Décoder les données base64 pour obtenir le fichier MP3
#     """
#     try:
#         logger.info(f"Requête API reçue - Génération audio - Voix: {voice}")
#         logger.debug(f"Texte reçu: {text[:100]}{'...' if len(text) > 100 else ''}")
        
#         if not text or not text.strip():
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Le texte ne peut pas être vide"
#             )
        
#         if len(text) > 5000:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Le texte ne peut pas dépasser 5000 caractères"
#             )
        
#         async def generate_audio_response():
#             logger.info(f"Début de génération audio MP3 - Voix: {voice}")
            
#             # Génération de l'audio avec Speechify (format MP3)
#             audio_data = await generate_speech(text, voice)
#             if not audio_data:
#                 logger.error("Échec de la génération audio")
#                 raise ValueError("Échec de la génération audio")
            
#             return {
#                 "audio_data": base64.b64encode(audio_data).decode(),
#                 "format": "mp3"
#             }
        
#         response = await asyncio.wait_for(
#             generate_audio_response(),
#             timeout=REQUEST_TIMEOUT
#         )
        
#         logger.info("Audio MP3 généré avec succès")
#         return {"status": "success", **response}
        
#     except asyncio.TimeoutError:
#         logger.error(f"Timeout lors de la génération audio avec la voix {voice}")
#         raise HTTPException(
#             status_code=status.HTTP_408_REQUEST_TIMEOUT,
#             detail="Timeout lors de la génération audio"
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Erreur lors de la génération audio : {str(e)}")
#         return {"status": "error", "message": "Une erreur interne s'est produite lors de la génération audio."}