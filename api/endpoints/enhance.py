import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.api_utils.security_utils import get_api_key
from config import LOGGER_NAME
from utils.handlers.images import upload_images
from utils.unified_image import Format, Transformation_Type, unified_image_transform

router = APIRouter()
logger = logging.getLogger(LOGGER_NAME)

@router.post("/image/enhance", tags=["image"], summary="Enhance image quality")
async def enhance_image_endpoint(
    image: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
    _api_key: Optional[str] = Depends(get_api_key),
):
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    logger.info(f"Image enhance request: user_id={user_id}")
    
    try:
        image_data = await image.read()
        urls = await upload_images([image_data])
        image_url = urls[0]
        if not image_url:
            raise HTTPException(status_code=400, detail="Failed to upload image")
        
        result = await unified_image_transform(
            transformations=[Transformation_Type.ENHANCE.value],
            format=Format.BASE64,
            image_url=image_url,
            user_id=user_id,
        )
        
        if result:
            return {"image": result}
        else:
            raise HTTPException(status_code=500, detail="Enhancement failed")
    except Exception as e:
        logger.error(f"Error in image enhancement: {e}")
        raise HTTPException(status_code=500, detail="Image enhancement failed")
