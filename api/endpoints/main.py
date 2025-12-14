import asyncio
import logging
import socket
from typing import Optional

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.api_utils.server_utils import is_https_api_running
from config import LOGGER_NAME, API_REQUEST_TIMEOUT
from utils.discord_utils.status import get_status

router = APIRouter()
logger = logging.getLogger(LOGGER_NAME)

@router.get("/", tags=["general"])
async def read_root(request: Request):
    """Main API entry point"""
    try:
        https_api = await asyncio.wait_for(
            is_https_api_running(), 
            timeout=API_REQUEST_TIMEOUT
        )
        https_status = "running" if https_api else "stopped"
        
        return {
            "message": "AlphaLLM API", 
            "version": "2.0.0", 
            "HTTP": "running", 
            "HTTPS": https_status,
            "authenticated": False,
            "client_ip": request.client.host if request.client else "unknown"
        }
    except asyncio.TimeoutError:
        logger.error("Timeout while checking HTTPS API status")
        return {
            "message": "AlphaLLM API", 
            "version": "2.0.0", 
            "HTTP": "running", 
            "HTTPS": "timeout",
            "authenticated": False
        }
    except Exception as e:
        logger.error(f"Error reading root endpoint: {str(e)}")
        return {"status": "error", "message": "An internal server error occurred."}

@router.get("/status", tags=["general"])
async def status_check():
    """API status check endpoint"""
    try:
        status_result = get_status()
        return status_result
    except Exception as e:
        logger.error(f"Error during status check: {str(e)}")
        return {"status": "error", "message": "An internal server error occurred."}