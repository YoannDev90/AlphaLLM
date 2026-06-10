"""Extract text from images with Tesseract OCR."""

import base64
import io
from typing import Optional

import pytesseract
import requests
from PIL import Image, ImageOps

from utils.logger import get_logger

logger = get_logger()


def _build_tesseract_config(psm: Optional[int], oem: Optional[int]) -> str:
    """Build a Tesseract command-line config string.

    Parameters
    ----------
    psm : Optional[int]
        Page segmentation mode value.
    oem : Optional[int]
        OCR engine mode value.

    Returns
    -------
    str
        Combined Tesseract config string.
    """
    parts = []
    if psm is not None:
        parts.append(f"--psm {psm}")
    if oem is not None:
        parts.append(f"--oem {oem}")
    return " ".join(parts)


def _load_image_bytes(
    image_path: Optional[str], image_url: Optional[str], image_base64: Optional[str]
) -> bytes:
    """Load raw image bytes from a path, URL or base64 payload.

    Parameters
    ----------
    image_path : Optional[str]
        Local filesystem path.
    image_url : Optional[str]
        Remote URL to fetch.
    image_base64 : Optional[str]
        Base64-encoded image payload.

    Returns
    -------
    bytes
        Raw image bytes.

    Raises
    ------
    ValueError
        If none of the image sources are provided.
    """
    if image_path:
        with open(image_path, "rb") as f:
            return f.read()

    if image_url:
        response = requests.get(image_url, timeout=20)
        response.raise_for_status()
        return response.content

    if image_base64:
        return base64.b64decode(image_base64)

    raise ValueError("Provide one source: image_path, image_url, or image_base64")


async def image_ocr(
    image_path: str = "",
    image_url: str = "",
    image_base64: str = "",
    lang: str = "eng",
    psm: Optional[int] = None,
    oem: Optional[int] = None,
) -> str:
    """Extract text from image with Tesseract OCR.

    Parameters
    ----------
    image_path : str
        Local image path to read (default: '').
    image_url : str
        Image URL to fetch (default: '').
    image_base64 : str
        Base64 image payload (default: '').
    lang : str
        Tesseract language code (default: 'eng').
    psm : Optional[int]
        Page segmentation mode (default: None).
    oem : Optional[int]
        OCR engine mode (default: None).

    Returns
    -------
    str
        Detected text or an error message.
    """
    try:
        raw = _load_image_bytes(image_path, image_url, image_base64)
        image = Image.open(io.BytesIO(raw))

        # Basic preprocessing improves OCR quality on screenshots/memes.
        image = ImageOps.grayscale(image)
        config = _build_tesseract_config(psm, oem)
        text = pytesseract.image_to_string(image, lang=lang, config=config)

        cleaned = text.strip()
        if not cleaned:
            return "No text detected in image."
        return cleaned
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract binary not found")
        return (
            "Error: Tesseract OCR is not installed on host (install `tesseract-ocr`)."
        )
    except Exception as e:
        logger.error(f"image_ocr failed: {e}")
        return f"Error: {str(e)}"
