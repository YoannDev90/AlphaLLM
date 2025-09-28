"""
Configuration de l'application FastAPI pour AlphaLLM
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging

from utils.config import API_HOST, API_PORT, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

def create_app() -> FastAPI:
    app = FastAPI(
        title="AlphaLLM API",
        description="API pour le projet AlphaLLM avec sécurité renforcée",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc", 
        openapi_tags=[
            {
                "name": "general",
                "description": "Endpoints généraux de l'API",
            },
            {
                "name": "generation",
                "description": "Endpoints de génération IA",
            },
            {
                "name": "info",
                "description": "Informations sur l'API",
            },
        ]
    )

    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.openapi = lambda: custom_openapi(app)
    
    return app

def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title="AlphaLLM API",
        version="1.0.0",
        description="""
        ## API AlphaLLM avec sécurité sélective
        
        Cette API nécessite une authentification par clé API uniquement pour les endpoints de génération.
        
        ### Endpoints publics (sans authentification)
        - `/` : Point d'entrée principal
        - `/status` : Statut de l'API  
        - `/text-models` : Liste des modèles de texte avec leurs capacités
        - `/image-models` : Liste des modèles d'image avec leurs spécifications
        - `/api/info` : Informations sur l'API
        - `/docs` : Documentation Swagger
        - `/redoc` : Documentation ReDoc
        
        ### Endpoints protégés (authentification requise)
        - `/generate/text` : Génération de texte avec un modèle spécifique
        - `/generate/image` : Génération d'image en format JSON/Base64
        - `/generate/image/binary` : Génération d'image en format binaire direct
        
        ### Authentification (pour les endpoints protégés)
        Vous pouvez vous authentifier de plusieurs façons :
        
        1. **Bearer Token** (Recommandé) : Utilisez le bouton "Authorize" ci-dessous
        2. **Header X-API-Key** : Ajoutez un header `X-API-Key: votre-clé`
        3. **Paramètre de requête** : Ajoutez `?api_key=votre-clé` à l'URL
        
        ### Rate Limiting
        - Limite : 10 requêtes par minute par clé API (endpoints protégés)
        - En cas de dépassement : Erreur 429
        """,
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": "Entrez votre clé API dans le champ ci-dessous"
        }
    }
    
    if "paths" in openapi_schema:
        for path, path_obj in openapi_schema["paths"].items():
            if "/generate/" in path:
                for method, method_obj in path_obj.items():
                    if method.lower() in ["get", "post", "put", "delete"]:
                        method_obj["security"] = [{"APIKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema