"""
Configuration de l'application FastAPI pour AlphaLLM
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import aiohttp
import asyncio
import random
import socket
import logging

from utils.config import API_HOST, API_PORT, LOGGER_NAME, REQUEST_TIMEOUT

logger = logging.getLogger(LOGGER_NAME)

# Configuration de la sécurité pour Swagger
bearer_scheme = HTTPBearer(
    scheme_name="API Key",
    description="Entrez votre clé API",
    bearerFormat="API Key"
)

def create_app() -> FastAPI:
    """Crée et configure l'application FastAPI"""
    app = FastAPI(
        title="AlphaLLM API",
        description="API pour le projet AlphaLLM avec sécurité renforcée",
        version="1.0.0",
        docs_url="/docs",  # Documentation Swagger
        redoc_url="/redoc",  # Documentation ReDoc
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

    # Middleware de sécurité
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]  # À configurer selon vos besoins
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # À restreindre en production
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Configuration OpenAPI personnalisée
    app.openapi = lambda: custom_openapi(app)
    
    return app

def custom_openapi(app: FastAPI):
    """Configuration OpenAPI personnalisée avec authentification"""
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
        
        ### Modèles disponibles
        **Texte** : mistral, openai, llama, deepseek, qwen, evilgpt, gemini, perplexity, grok, claude, cohere, glm, kimi, phi
        
        **Image** : dalle, flux, sdxl, playground, recraft, imagen, phoenix, grokimage, gptimage, sana, kontext, nsfw
        """,
        routes=app.routes,
    )
    
    # Ajoute le schéma d'authentification Bearer
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": "Entrez votre clé API dans le champ ci-dessous"
        }
    }
    
    # Applique la sécurité sélectivement aux endpoints de génération
    if "paths" in openapi_schema:
        for path, path_obj in openapi_schema["paths"].items():
            # Applique l'authentification uniquement aux endpoints de génération
            if "/generate/" in path:
                for method, method_obj in path_obj.items():
                    if method.lower() in ["get", "post", "put", "delete"]:
                        method_obj["security"] = [{"APIKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

async def ping_https_server(url: str, interval_range: tuple = (30, 300)):
    """
    Envoie des requêtes ping à un serveur HTTPS à intervalles aléatoires avec timeout
    
    Args:
        url (str): L'URL du serveur à pinger
        interval_range (tuple): Plage d'intervalles en secondes (min, max)
    """
    min_interval, max_interval = interval_range
    
    if min_interval < 30 or max_interval > 300 or min_interval >= max_interval:
        return
        
    while True:
        try:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(url) as response:
                    end_time = asyncio.get_event_loop().time()
                    ping_time = (end_time - start_time) * 1000
                    
                    if response.status != 200:
                        logger.warning(f"Ping vers {url} - Status: {response.status} - {ping_time:.2f}ms")
                        
        except asyncio.TimeoutError:
            logger.error(f"Ping vers {url} - Timeout")
        except Exception as e:
            logger.error(f"Ping vers {url} - Erreur: {str(e)}")
        
        next_interval = random.randint(min_interval, max_interval)
        logger.debug(f"Prochain ping dans {next_interval}s")
        await asyncio.sleep(next_interval)

def get_server_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"