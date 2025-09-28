from fastapi import APIRouter, Depends
from typing import Optional
from api.utils.models_utils import load_models_data

router = APIRouter()

@router.get("/text-models", tags=["info"])
async def get_text_models():
    text_models = load_models_data("text")
    
    return {
        "status": "success",
        "count": len(text_models),
        "models": text_models,
        "default_model": "llama"
    }

@router.get("/image-models", tags=["info"])
async def get_image_models():
    image_models = load_models_data("image")
    
    return {
        "status": "success",
        "count": len(image_models),
        "models": image_models,
        "supported_formats": ["PNG", "JPEG", "SVG"],
        "common_sizes": ["512x512", "768x768", "1024x1024"],
        "note": "Vérifiez les capacités spécifiques de chaque modèle avant utilisation"
    }

@router.get("/api/info", tags=["info"])
async def api_info():
    from utils.config import API_KEY_REQUIRED, MAX_REQUESTS_PER_MINUTE, REQUEST_TIMEOUT
    
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
            "/text-models": "Liste des modèles de texte disponibles (public)",
            "/image-models": "Liste des modèles d'image disponibles (public)",
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