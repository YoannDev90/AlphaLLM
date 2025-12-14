import asyncio
import logging

from fastapi import APIRouter, Request

from api.api_utils.server_utils import is_https_api_running
from config import LOGGER_NAME, API_REQUEST_TIMEOUT

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