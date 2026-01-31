import logging

from fastapi import APIRouter

from config import LOGGER_NAME
from utils.discord_utils.status import get_status

router = APIRouter()
logger = logging.getLogger(LOGGER_NAME)


@router.get("/status", tags=["general"])
async def status_check():
    """API status check endpoint"""
    try:
        status_result = get_status()
        return status_result
    except Exception as e:
        logger.error(f"Error during status check: {str(e)}")
        return {"status": "error", "message": "An internal server error occurred."}
