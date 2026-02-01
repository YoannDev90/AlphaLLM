import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException

from api.api_utils.models_utils import load_models_data
from api.api_utils.security_utils import get_api_key
from config import LOGGER_NAME
from utils.unified_image import Format, unified_image_gen

router = APIRouter()
logger = logging.getLogger(LOGGER_NAME)


@router.post("/image/generation", tags=["image"], summary="Generate images from prompt")
async def generate_image(
    prompt: str = Form(...),
    model: Optional[str] = Form("flux"),
    num_images: int = Form(1),
    size: str = Form("1024x1024"),
    style: Optional[str] = Form(None),
    enhance: bool = Form(True),
    user_id: Optional[int] = Form(None),
    _api_key: Optional[str] = Depends(get_api_key),
):
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id is required")

    image_models = load_models_data("image")
    if model not in image_models:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not available for image generation",
        )

    logger.info(
        f"Image generation request: user_id={user_id}, model={model}, num_images={num_images}, size={size}, style={style}, enhance={enhance}, prompt={prompt[:50]}..."
    )

    try:
        results = await unified_image_gen(
            prompt=prompt,
            model=model,
            num_images=num_images,
            size=size,
            style=style,
            enhance=enhance,
            format=Format.BASE64,
            user_id=user_id,
        )

        images = [img for img, _ in results]
        models_used = [model for _, model in results]

        return {"images": images, "models": models_used}
    except Exception as e:
        logger.error(f"Error in image generation: {e}")
        raise HTTPException(status_code=500, detail="Image generation failed")
