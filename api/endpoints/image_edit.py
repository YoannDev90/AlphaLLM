import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.api_utils.models_utils import load_models_data
from api.api_utils.security_utils import get_api_key
from config import LOGGER_NAME
from utils.handlers.images import upload_images
from utils.unified_image import Format, unified_image_edit

router = APIRouter()
logger = logging.getLogger(LOGGER_NAME)

@router.post("/image/edit", tags=["image"], summary="Edit image with prompt")
async def edit_image(
    prompt: str = Form(...),
    model: Optional[str] = Form("gptimage"),
    num_images: int = Form(1),
    enhance: bool = Form(True),
    image: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
    _api_key: Optional[str] = Depends(get_api_key),
):
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    image_models = load_models_data("image")
    if model not in image_models:
        raise HTTPException(status_code=400, detail=f"Model '{model}' is not available for image editing")
    
    logger.info(f"Image edit request: user_id={user_id}, model={model}, num_images={num_images}, enhance={enhance}, prompt={prompt[:50]}...")
    
    try:
        image_data = await image.read()
        urls = await upload_images([image_data])
        image_url = urls[0]
        if not image_url:
            raise HTTPException(status_code=400, detail="Failed to upload image")
        
        results = await unified_image_edit(
            prompt=prompt,
            model=model,
            num_images=num_images,
            enhance=enhance,
            format=Format.BASE64,
            images_url=[image_url],
            user_id=user_id,
        )
        
        images = [img for img, _ in results]
        models_used = [model for _, model in results]
        
        return {
            "images": images,
            "models": models_used
        }
    except Exception as e:
        logger.error(f"Error in image editing: {e}")
        raise HTTPException(status_code=500, detail="Image editing failed")
