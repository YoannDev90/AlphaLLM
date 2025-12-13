import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from api.api_utils.models_utils import load_models_data
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
router = APIRouter()

@router.get("/text/models", tags=["text"])
async def get_text_models():
    try:
        text_models = load_models_data("text")
        
        return {
            "status": "success",
            "count": len(text_models),
            "models": text_models,
            "default_model": "auto"
        }
    except Exception as e:
        logger.error(f"Error retrieving text models: {str(e)}")
        return {
            "status": "error",
            "message": "Error retrieving text models"
        }

@router.get("/image/models", tags=["image"])
async def get_image_models():
    try:
        image_models = load_models_data("image")
        
        return {
            "status": "success",
            "count": len(image_models),
            "models": image_models,
            "default_model": "flux"
        }
    except Exception as e:
        logger.error(f"Error retrieving image models: {str(e)}")
        return {
            "status": "error",
            "message": "Error retrieving image models"
        }