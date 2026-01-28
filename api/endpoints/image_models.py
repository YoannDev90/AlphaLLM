import logging

from fastapi import APIRouter

from api.api_utils.models_utils import load_models_data
from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
router = APIRouter()


@router.get("/image/models", tags=["image"])
async def get_image_models():
    try:
        image_models = load_models_data("image")

        return {
            "status": "success",
            "count": len(image_models),
            "models": image_models,
            "default_model": "flux",
        }
    except Exception as e:
        logger.error(f"Error retrieving image models: {str(e)}")
        return {"status": "error", "message": "Error retrieving image models"}
