from fastapi import APIRouter, Request, Depends, HTTPException, status
from typing import Optional
import asyncio
import aiohttp
import socket

from . import logger, REQUEST_TIMEOUT
from api.utils.server_utils import get_server_ip, is_https_api_running
from utils.status import get_status

router = APIRouter()

@router.get("/", tags=["general"])
async def read_root(request: Request):
    """Point d'entrée principal de l'API"""
    try:
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
            "authenticated": False,
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
        return {"status": "error", "message": "An internal server error occurred."}

@router.get("/status", tags=["general"])
async def status_check():
    """Point de contrôle de statut de l'API"""
    try:
        status_result = get_status()
        return status_result
    except Exception as e:
        logger.error(f"Erreur lors du point de contrôle de statut : {str(e)}")
        return {"status": "error", "message": str(e)}