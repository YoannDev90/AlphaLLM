"""FastAPI helpers that guard the routes with API keys."""

import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from config import API_KEY_REQUIRED, API_KEYS, API_KEYS_MAPPING, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

bearer_scheme = HTTPBearer(
    scheme_name="API Key", description="Enter your API key", bearerFormat="API Key"
)


def get_api_key(request: Request) -> Optional[str]:
    """Extract the API key from headers or query parameters."""
    if not API_KEY_REQUIRED:
        logger.debug("API authentication disabled")
        return None

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        auth_header = request.headers.get("Authorization") or ""
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]

    if not api_key:
        api_key = request.query_params.get("api_key")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "API key required. Provide X-API-Key, Authorization: Bearer <key>, "
                "or ?api_key=<key>"
            ),
        )

    if not verify_api_access(api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key"
        )

    return api_key


def verify_api_access(api_key: str) -> bool:
    """Validate the API key against the allowed list."""
    if not API_KEY_REQUIRED:
        return True

    if not api_key:
        logger.warning("Attempt to authenticate with empty key")
        return False

    is_valid = api_key in API_KEYS
    if is_valid:
        user = next(
            (name for name, key in API_KEYS_MAPPING.items() if key == api_key),
            "unknown user",
        )
        logger.info(f"API authentication successful for {user}")
    else:
        logger.warning(f"Invalid API key used: {api_key[:8]}***")

    return is_valid
