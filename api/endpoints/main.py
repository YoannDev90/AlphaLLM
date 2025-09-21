"""
Endpoints principaux de l'API AlphaLLM
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from typing import Optional
import asyncio
import aiohttp
import socket

from . import get_api_key, verify_api_access, logger, REQUEST_TIMEOUT
from utils.status import get_status

router = APIRouter()

@router.get("/", tags=["general"])
async def read_root(request: Request):
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
            "authenticated": False,  # Endpoint public
            "client_ip": request.client.host if request.client else "unknown"
        }
    except asyncio.TimeoutError:
        logger.error("Timeout lors de la vérification de l'API HTTPS")
        return {
            "message": "AlphaLLM API", 
            "version": "1.0.0", 
            "HTTP": "running", 
            "HTTPS": "timeout",
            "authenticated": False
        }
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de la racine : {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/status", tags=["general"])
async def status_check():
    """Point de contrôle de statut de l'API"""
    try:
        status_result = get_status()
        return status_result
    except Exception as e:
        logger.error(f"Erreur lors du point de contrôle de statut : {str(e)}")
        return {"status": "error", "message": str(e)}

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