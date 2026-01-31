import logging
import random
from typing import List, Optional, Union

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Response,
                     UploadFile)
from fastapi.responses import StreamingResponse

from api.api_utils.security_utils import get_api_key
from config import AVAILABLE_MODELS, LOGGER_NAME
from utils.unified_text import Origin, unified_text_gen

router = APIRouter()
logger = logging.getLogger(LOGGER_NAME)


@router.post("/text/generation", tags=["text"], summary="Generate text from prompt")
async def generate_text(
    prompt: str = Form(...),
    model: Optional[str] = Form("auto"),
    user_id: Optional[int] = Form(None),
    conv_id: Optional[int] = Form(None),
    stream: bool = Form(False),
    files: Optional[Union[List[UploadFile], str]] = File(None),
    _api_key: Optional[str] = Depends(get_api_key),
):
    """Generate text using the AI pipeline with optional files and history."""
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id is required")

    if conv_id is None:
        raise HTTPException(status_code=400, detail="conv_id is required")

    if model not in AVAILABLE_MODELS and model != "auto":
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not available for text generation",
        )

    if conv_id <= 0:
        conv_id = random.randint(1, 2**31 - 1)
    if user_id <= 0:
        user_id = random.randint(1, 2**31 - 1)

    logger.info(
        f"Text generation request: user_id={user_id}, conv_id={conv_id}, model={model}, stream={stream}, prompt={prompt[:50]}..."
    )
    logger.info(
        f"Files received: {[file.filename for file in files] if isinstance(files, list) else files}"
    )

    if stream:

        async def generate():
            logger.debug("Starting streaming text generation")
            try:
                async for result in unified_text_gen(
                    user_id=user_id,
                    conv_id=str(conv_id),
                    input=prompt,
                    model=model,
                    origin=Origin.API,
                    stream=True,
                    files=files if isinstance(files, list) else None,
                ):
                    if hasattr(result, "chunk") and result.chunk:
                        logger.debug(f"Yielding chunk: {result.chunk[:50]}...")
                        yield result.chunk
            except Exception as e:
                logger.error(f"Error in streaming text generation: {e}")
                yield f"Error: {str(e)}"
            logger.info("Streaming generation finished")

        return StreamingResponse(generate(), media_type="text/plain")
    else:
        logger.debug("Starting non-streaming text generation")
        full_text = ""
        try:
            result = None
            async for r in unified_text_gen(
                user_id=user_id,
                conv_id=str(conv_id),
                input=prompt,
                model=model,
                origin=Origin.API,
                stream=False,
                files=files if isinstance(files, list) else None,
            ):
                result = r
                break
            if result and hasattr(result, "response"):
                full_text = result.response
            else:
                full_text = "No response generated"
        except Exception as e:
            logger.error(f"Error in non-streaming text generation: {e}")
            full_text = f"Error: {str(e)}"
        logger.info("Non-streaming generation finished")
        return Response(content=full_text, media_type="text/plain")
