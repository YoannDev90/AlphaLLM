import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import Response
from utils.status import get_status
from utils.config import API_HOST, API_PORT, LOGGER_NAME, REQUEST_TIMEOUT
from utils.security import get_api_key, verify_api_access
import asyncio
import logging
import socket
import aiohttp
import random
import base64
from typing import Optional

logger = logging.getLogger(LOGGER_NAME)

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

# Configuration de la sécurité pour Swagger
bearer_scheme = HTTPBearer(
    scheme_name="API Key",
    description="Entrez votre clé API",
    bearerFormat="API Key"
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

@app.get("/", tags=["general"])
async def read_root(request: Request, api_key: Optional[str] = Depends(get_api_key)):
    """Point d'entrée principal de l'API"""
    try:
        # Applique un timeout sur l'opération
        https_api = await asyncio.wait_for(
            is_https_api_running(), 
            timeout=REQUEST_TIMEOUT
        )
        https_status = "running" if https_api else "stopped"
        
        return {
            "message": "AlphaLLM API", 
            "version": "1.0.0", 
            "HTTP": "running", 
            "HTTPS": https_status,
            "authenticated": verify_api_access(api_key),
            "client_ip": request.client.host if request.client else "unknown"
        }
    except asyncio.TimeoutError:
        logger.error("Timeout lors de la vérification de l'API HTTPS")
        return {
            "message": "AlphaLLM API", 
            "version": "1.0.0", 
            "HTTP": "running", 
            "HTTPS": "timeout",
            "authenticated": verify_api_access(api_key)
        }
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de la racine : {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/status", tags=["general"])
async def status_check(api_key: Optional[str] = Depends(get_api_key)):
    """Point de contrôle de statut de l'API"""
    try:
        status = await asyncio.wait_for(
            asyncio.create_task(get_status()), 
            timeout=REQUEST_TIMEOUT
        )
        return status
    except asyncio.TimeoutError:
        logger.error("Timeout lors du contrôle de statut")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Timeout lors de la récupération du statut"
        )
    except Exception as e:
        logger.error(f"Erreur lors du point de contrôle de statut : {str(e)}")
        return {"status": "error", "message": str(e)}
    
@app.get("/generate/image", tags=["generation"])
async def generate_image(
    model: str, 
    prompt: str, 
    size: str,
    api_key: Optional[str] = Depends(get_api_key)
):
    """
    Génère une image avec timeout et authentification
    
    - **model**: Modèle d'IA à utiliser pour la génération
    - **prompt**: Description de l'image à générer
    - **size**: Taille de l'image souhaitée
    """
    try:
        from utils.image_gen import generate_image
        
        response = await asyncio.wait_for(
            generate_image(prompt=prompt, model=model, size=size),
            timeout=REQUEST_TIMEOUT * 2
        )
        
        # Vérifiez le type de réponse
        if response is None:
            return {"status": "error", "message": "Échec de la génération d'image"}
        
        # Si response est un tuple (image_data, bool)
        if isinstance(response, tuple):
            image_data, is_url = response
            
            if is_url or isinstance(image_data, str):
                # Si c'est une URL ou une chaîne, retournez-la directement
                return {"status": "success", "image_url": image_data}
            elif isinstance(image_data, bytes):
                # Si ce sont des bytes, encodez en base64
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
            # Gestion d'autres types de réponse
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

@app.get("/generate/image/binary", tags=["generation"])
async def generate_image_binary(
    model: str, 
    prompt: str, 
    size: str,
    api_key: Optional[str] = Depends(get_api_key)
):
    """
    Génère une image et la retourne directement en format binaire
    
    - **model**: Modèle d'IA à utiliser pour la génération
    - **prompt**: Description de l'image à générer
    - **size**: Taille de l'image souhaitée
    
    Retourne l'image directement comme fichier binaire (PNG/JPEG)
    """
    try:
        from utils.image_gen import generate_image
        
        response = await asyncio.wait_for(
            generate_image(prompt=prompt, model=model, size=size),
            timeout=REQUEST_TIMEOUT * 2
        )
        
        if response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Échec de la génération d'image"
            )
        
        # Si response est un tuple (image_data, bool)
        if isinstance(response, tuple):
            image_data, is_url = response
            
            if isinstance(image_data, bytes):
                # Retourne l'image directement en binaire
                return Response(
                    content=image_data,
                    media_type="image/png",
                    headers={"Content-Disposition": "inline; filename=generated_image.png"}
                )
            elif is_url or isinstance(image_data, str):
                # Si c'est une URL, redirige vers celle-ci
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Image disponible via URL",
                    headers={"Location": image_data}
                )
        elif isinstance(response, bytes):
            return Response(
                content=response,
                media_type="image/png",
                headers={"Content-Disposition": "inline; filename=generated_image.png"}
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Format d'image non supporté"
        )
                
    except asyncio.TimeoutError:
        logger.error(f"Timeout lors de la génération de l'image avec le modèle {model}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Timeout lors de la génération de l'image"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'image : {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )
    
@app.get("/generate/text", tags=["generation"])
async def generate_text(
    model: str, 
    prompt: str,
    api_key: Optional[str] = Depends(get_api_key)
):
    """
    Génère un texte avec timeout et authentification
    
    - **model**: Modèle d'IA à utiliser (mistral, openai, llama, deepseek, qwen, etc.)
    - **prompt**: Texte d'entrée pour la génération
    """
    try:
        from models.text.mistral import mistral_chat
        from models.text.deepseek import deepseek_chat
        from models.text.qwen import qwen_chat
        from models.text.openai import openai_chat
        from models.text.evilgpt import evilgpt_chat
        from models.text.llama import llama_chat
        from models.text.gemini import gemini_chat
        from models.text.perplexity import perplexity_chat
        from models.text.grok import grok_chat
        from models.text.claude import claude_chat
        from models.text.cohere import cohere_chat
        from models.text.glm import glm_chat
        from models.text.kimi import kimi_chat
        from models.text.phi import phi_chat
                
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        parameters = {
            "history": False, 
            "preprompt": False, 
            "tools": False, 
            "internet": False, 
            "raw": False
        }
        
        # Fonction de génération selon le modèle
        async def generate_response():
            match model.lower():
                case "mistral":
                    response = await mistral_chat(messages, parameters)
                    logger.info("Réponse générée par Mistral")
                case "deepseek":
                    response = await deepseek_chat(messages, parameters)
                    logger.info("Réponse générée par DeepSeek")
                case "qwen":
                    response = await qwen_chat(messages, parameters)
                    logger.info("Réponse générée par Qwen")
                case "openai":
                    response = await openai_chat(messages, parameters)
                    logger.info("Réponse générée par OpenAI")
                case "evilgpt":
                    response = await evilgpt_chat(messages, parameters)
                    logger.info("Réponse générée par EvilGPT")
                case "llama":
                    response = await llama_chat(messages, parameters)
                    logger.info("Réponse générée par Llama")
                case "gemini":
                    response = await gemini_chat(messages, parameters)
                    logger.info("Réponse générée par Gemini")
                case "perplexity":
                    response = await perplexity_chat(messages, parameters)
                    logger.info("Réponse générée par Perplexity")
                case "grok":
                    response = await grok_chat(messages, parameters)
                    logger.info("Réponse générée par Grok")
                case "claude":
                    response = await claude_chat(messages, parameters)
                    logger.info("Réponse générée par Claude")
                case "cohere":
                    response = await cohere_chat(messages, parameters)
                    logger.info("Réponse générée par Cohere")
                case "glm":
                    response = await glm_chat(messages, parameters)
                    logger.info("Réponse générée par GLM")
                case "kimi":
                    response = await kimi_chat(messages, parameters)
                    logger.info("Réponse générée par Kimi")
                case "phi":
                    response = await phi_chat(messages, parameters)
                    logger.info("Réponse générée par Phi")
                case _:
                    response = await llama_chat(messages, parameters)
                    logger.info("Réponse générée par Llama (modèle par défaut)")
            return response
        
        # Applique un timeout sur la génération de texte
        response = await asyncio.wait_for(
            generate_response(),
            timeout=REQUEST_TIMEOUT
        )
        
        return {"status": "success", "response": response}
    except asyncio.TimeoutError:
        logger.error(f"Timeout lors de la génération de texte avec le modèle {model}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Timeout lors de la génération de texte"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la génération du texte : {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/text-models", tags=["info"])
async def get_text_models(api_key: Optional[str] = Depends(get_api_key)):
    """
    Retourne la liste des modèles de texte disponibles
    
    Fournit une liste complète des modèles d'IA texte supportés,
    avec leurs capacités et caractéristiques principales.
    """
    text_models = {
        "mistral": {
            "name": "Mistral AI",
            "description": "Modèle français de pointe pour la génération de texte",
            "capabilities": ["chat", "completion", "multilingual"],
            "languages": ["français", "anglais", "espagnol", "allemand", "italien"],
            "max_tokens": 32768,
            "supports_tools": True,
            "supports_streaming": True
        },
        "openai": {
            "name": "OpenAI GPT",
            "description": "Modèle GPT d'OpenAI pour conversations et completion",
            "capabilities": ["chat", "completion", "code", "reasoning"],
            "languages": ["multilingue"],
            "max_tokens": 128000,
            "supports_tools": True,
            "supports_streaming": True
        },
        "claude": {
            "name": "Anthropic Claude",
            "description": "Assistant IA constitutionnel d'Anthropic",
            "capabilities": ["chat", "analysis", "reasoning", "code"],
            "languages": ["multilingue"],
            "max_tokens": 200000,
            "supports_tools": True,
            "supports_streaming": True
        },
        "llama": {
            "name": "Meta LLaMA",
            "description": "Modèle open-source de Meta pour diverses tâches",
            "capabilities": ["chat", "completion", "code"],
            "languages": ["multilingue"],
            "max_tokens": 8192,
            "supports_tools": False,
            "supports_streaming": True
        },
        "deepseek": {
            "name": "DeepSeek",
            "description": "Modèle spécialisé en code et raisonnement",
            "capabilities": ["chat", "code", "reasoning", "math"],
            "languages": ["anglais", "chinois"],
            "max_tokens": 32768,
            "supports_tools": True,
            "supports_streaming": True
        },
        "qwen": {
            "name": "Alibaba Qwen",
            "description": "Modèle multilingue d'Alibaba",
            "capabilities": ["chat", "completion", "multilingual"],
            "languages": ["chinois", "anglais", "japonais", "coréen"],
            "max_tokens": 32768,
            "supports_tools": True,
            "supports_streaming": True
        },
        "gemini": {
            "name": "Google Gemini",
            "description": "Modèle multimodal de Google",
            "capabilities": ["chat", "vision", "code", "reasoning"],
            "languages": ["multilingue"],
            "max_tokens": 2000000,
            "supports_tools": True,
            "supports_streaming": True
        },
        "grok": {
            "name": "xAI Grok",
            "description": "Modèle d'IA de xAI avec accès temps réel",
            "capabilities": ["chat", "real-time", "humor"],
            "languages": ["anglais"],
            "max_tokens": 131072,
            "supports_tools": True,
            "supports_streaming": True
        },
        "perplexity": {
            "name": "Perplexity AI",
            "description": "Moteur de recherche IA avec sources",
            "capabilities": ["search", "research", "citations"],
            "languages": ["multilingue"],
            "max_tokens": 4096,
            "supports_tools": True,
            "supports_streaming": True
        },
        "cohere": {
            "name": "Cohere",
            "description": "Modèle enterprise de Cohere",
            "capabilities": ["chat", "classification", "embedding"],
            "languages": ["multilingue"],
            "max_tokens": 4096,
            "supports_tools": True,
            "supports_streaming": True
        },
        "evilgpt": {
            "name": "EvilGPT",
            "description": "Modèle personnalisé sans restrictions",
            "capabilities": ["chat", "unrestricted"],
            "languages": ["multilingue"],
            "max_tokens": 4096,
            "supports_tools": False,
            "supports_streaming": True
        },
        "glm": {
            "name": "ChatGLM",
            "description": "Modèle bilingue chinois-anglais",
            "capabilities": ["chat", "completion"],
            "languages": ["chinois", "anglais"],
            "max_tokens": 32768,
            "supports_tools": True,
            "supports_streaming": True
        },
        "kimi": {
            "name": "Moonshot Kimi",
            "description": "Modèle avec très long contexte",
            "capabilities": ["chat", "long-context"],
            "languages": ["chinois", "anglais"],
            "max_tokens": 200000,
            "supports_tools": True,
            "supports_streaming": True
        },
        "phi": {
            "name": "Microsoft Phi",
            "description": "Petit modèle efficace de Microsoft",
            "capabilities": ["chat", "code", "reasoning"],
            "languages": ["anglais"],
            "max_tokens": 131072,
            "supports_tools": False,
            "supports_streaming": True
        }
    }
    
    return {
        "status": "success",
        "count": len(text_models),
        "models": text_models,
        "default_model": "llama"
    }

@app.get("/image-models", tags=["info"])
async def get_image_models(api_key: Optional[str] = Depends(get_api_key)):
    """
    Retourne la liste des modèles d'image disponibles
    
    Fournit une liste complète des modèles d'IA image supportés,
    avec leurs capacités, tailles supportées et caractéristiques.
    """
    image_models = {
        "dalle": {
            "name": "DALL-E 3",
            "description": "Générateur d'images avancé d'OpenAI",
            "provider": "OpenAI/ElectronHub",
            "capabilities": ["text-to-image", "high-quality", "photorealistic"],
            "supported_sizes": ["1024x1024", "1792x1024", "1024x1792"],
            "quality_options": ["standard", "hd"],
            "max_prompt_length": 4000,
            "output_formats": ["PNG", "JPEG"],
            "nsfw_filter": True
        },
        "flux": {
            "name": "Flux",
            "description": "Modèle de génération d'images open-source",
            "provider": "Black Forest Labs",
            "capabilities": ["text-to-image", "fast-generation"],
            "supported_sizes": ["512x512", "768x768", "1024x1024"],
            "quality_options": ["standard"],
            "max_prompt_length": 2000,
            "output_formats": ["PNG"],
            "nsfw_filter": False
        },
        "sdxl": {
            "name": "Stable Diffusion XL",
            "description": "Version améliorée de Stable Diffusion",
            "provider": "Stability AI",
            "capabilities": ["text-to-image", "style-transfer", "inpainting"],
            "supported_sizes": ["512x512", "768x768", "1024x1024", "1152x896", "896x1152"],
            "quality_options": ["standard", "high"],
            "max_prompt_length": 77,
            "output_formats": ["PNG", "JPEG"],
            "nsfw_filter": True
        },
        "playground": {
            "name": "Playground AI",
            "description": "Modèle artistique et créatif",
            "provider": "Playground AI",
            "capabilities": ["text-to-image", "artistic", "creative"],
            "supported_sizes": ["512x512", "768x768", "1024x1024"],
            "quality_options": ["standard"],
            "max_prompt_length": 1000,
            "output_formats": ["PNG"],
            "nsfw_filter": True
        },
        "recraft": {
            "name": "Recraft",
            "description": "Générateur d'images vectorielles et designs",
            "provider": "Recraft",
            "capabilities": ["text-to-image", "vector", "design", "logos"],
            "supported_sizes": ["512x512", "1024x1024", "1024x768", "768x1024"],
            "quality_options": ["standard", "vector"],
            "max_prompt_length": 500,
            "output_formats": ["PNG", "SVG"],
            "nsfw_filter": True
        },
        "imagen": {
            "name": "Google Imagen",
            "description": "Générateur d'images de Google",
            "provider": "Google",
            "capabilities": ["text-to-image", "photorealistic", "detailed"],
            "supported_sizes": ["512x512", "1024x1024"],
            "quality_options": ["standard"],
            "max_prompt_length": 1024,
            "output_formats": ["PNG"],
            "nsfw_filter": True
        },
        "phoenix": {
            "name": "Phoenix",
            "description": "Modèle de génération d'images personnalisé",
            "provider": "Custom",
            "capabilities": ["text-to-image", "fantasy", "sci-fi"],
            "supported_sizes": ["512x512", "768x768", "1024x1024"],
            "quality_options": ["standard"],
            "max_prompt_length": 800,
            "output_formats": ["PNG"],
            "nsfw_filter": False
        },
        "grokimage": {
            "name": "Grok Image",
            "description": "Générateur d'images de xAI",
            "provider": "xAI",
            "capabilities": ["text-to-image", "humor", "memes"],
            "supported_sizes": ["512x512", "1024x1024"],
            "quality_options": ["standard"],
            "max_prompt_length": 2000,
            "output_formats": ["PNG"],
            "nsfw_filter": True
        },
        "gptimage": {
            "name": "GPT Image",
            "description": "Générateur d'images basé sur GPT",
            "provider": "Custom",
            "capabilities": ["text-to-image", "conversational"],
            "supported_sizes": ["512x512", "1024x1024"],
            "quality_options": ["standard"],
            "max_prompt_length": 1500,
            "output_formats": ["PNG"],
            "nsfw_filter": True
        },
        "sana": {
            "name": "Sana",
            "description": "Modèle de génération d'images artistiques",
            "provider": "Custom",
            "capabilities": ["text-to-image", "artistic", "anime"],
            "supported_sizes": ["512x512", "768x768", "1024x1024"],
            "quality_options": ["standard", "artistic"],
            "max_prompt_length": 1000,
            "output_formats": ["PNG"],
            "nsfw_filter": False
        },
        "kontext": {
            "name": "Kontext",
            "description": "Générateur d'images contextuel",
            "provider": "Custom",
            "capabilities": ["text-to-image", "context-aware"],
            "supported_sizes": ["512x512", "1024x1024"],
            "quality_options": ["standard"],
            "max_prompt_length": 800,
            "output_formats": ["PNG"],
            "nsfw_filter": True
        },
        "nsfw": {
            "name": "NSFW Generator",
            "description": "Générateur d'images sans filtres (NSFW)",
            "provider": "Custom",
            "capabilities": ["text-to-image", "unfiltered", "adult"],
            "supported_sizes": ["512x512", "768x768", "1024x1024"],
            "quality_options": ["standard"],
            "max_prompt_length": 1000,
            "output_formats": ["PNG"],
            "nsfw_filter": False,
            "warning": "Contenu adulte non filtré"
        }
    }
    
    return {
        "status": "success",
        "count": len(image_models),
        "models": image_models,
        "supported_formats": ["PNG", "JPEG", "SVG"],
        "common_sizes": ["512x512", "768x768", "1024x1024"],
        "note": "Vérifiez les capacités spécifiques de chaque modèle avant utilisation"
    }

@app.get("/api/info", tags=["info"])
async def api_info(api_key: Optional[str] = Depends(get_api_key)):
    """
    Informations sur l'API et l'authentification
    
    Retourne des informations détaillées sur la configuration de l'API,
    les limites de taux, les méthodes d'authentification et les endpoints disponibles.
    """
    from utils.config import API_KEY_REQUIRED, MAX_REQUESTS_PER_MINUTE, REQUEST_TIMEOUT
    
    return {
        "api_version": "1.0.0",
        "authentication_required": API_KEY_REQUIRED,
        "rate_limit": {
            "max_requests_per_minute": MAX_REQUESTS_PER_MINUTE,
            "window_seconds": 60
        },
        "timeout_seconds": REQUEST_TIMEOUT,
        "authenticated": verify_api_access(api_key),
        "endpoints": {
            "/": "Point d'entrée principal",
            "/status": "Statut de l'API",
            "/generate/text": "Génération de texte",
            "/generate/image": "Génération d'image (JSON avec base64)",
            "/generate/image/binary": "Génération d'image (binaire direct)",
            "/text-models": "Liste des modèles de texte disponibles",
            "/image-models": "Liste des modèles d'image disponibles",
            "/api/info": "Informations sur l'API",
            "/docs": "Documentation Swagger",
            "/redoc": "Documentation ReDoc"
        },
        "authentication_methods": [
            "Header: Authorization: Bearer <api_key>",
            "Header: X-API-Key: <api_key>",
            "Query parameter: ?api_key=<api_key>"
        ]
    }

async def start_api_async(host: str = API_HOST, port: int = API_PORT):
    """
    Version asynchrone pour démarrer l'API dans une boucle d'événements existante
    """
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="error",
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.info(f"API démarrée sur {get_server_ip()}:{port}")
    await server.serve()

def get_server_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

async def is_https_api_running():
    """Vérifie si l'API HTTPS est en cours d'exécution avec timeout"""
    try:
        timeout = aiohttp.ClientTimeout(total=10)  # Timeout de 10 secondes
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("https://alphallm-api.onrender.com/status") as response:
                return response.status == 200
    except Exception:
        return False

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

# Configuration OpenAPI personnalisée pour l'authentification
def custom_openapi():
    """Configuration OpenAPI personnalisée avec authentification"""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title="AlphaLLM API",
        version="1.0.0",
        description="""
        ## API AlphaLLM avec sécurité renforcée
        
        Cette API nécessite une authentification par clé API pour accéder aux endpoints.
        
        ### Authentification
        Vous pouvez vous authentifier de plusieurs façons :
        
        1. **Bearer Token** (Recommandé) : Utilisez le bouton "Authorize" ci-dessous
        2. **Header X-API-Key** : Ajoutez un header `X-API-Key: votre-clé`
        3. **Paramètre de requête** : Ajoutez `?api_key=votre-clé` à l'URL
        
        ### Rate Limiting
        - Limite : 10 requêtes par minute par clé API
        - En cas de dépassement : Erreur 429
        
        ### Endpoints disponibles
        - `/text-models` : Liste des modèles de texte avec leurs capacités
        - `/image-models` : Liste des modèles d'image avec leurs spécifications
        - `/generate/text` : Génération de texte avec un modèle spécifique
        - `/generate/image` : Génération d'image en format JSON/Base64
        - `/generate/image/binary` : Génération d'image en format binaire direct
        
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
    
    # Applique la sécurité à tous les endpoints sauf ceux publics
    if "security" not in openapi_schema:
        openapi_schema["security"] = [{"APIKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Applique la configuration OpenAPI personnalisée
app.openapi = custom_openapi