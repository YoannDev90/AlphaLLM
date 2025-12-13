"""FastAPI helpers that guard the routes with API keys."""

import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from config import API_KEY_REQUIRED, API_KEYS, API_KEYS_MAPPING, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

bearer_scheme = HTTPBearer(
    scheme_name="API Key",
    description="Entrez votre clé API",
    bearerFormat="API Key"
)


def get_api_key(request: Request) -> Optional[str]:
    """Extract the API key from headers or query parameters."""
    if not API_KEY_REQUIRED:
        logger.debug("Authentification API désactivée")
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
            detail="Clé API requise. Fournissez X-API-Key, Authorization: Bearer <clé>, ou ?api_key=<clé>"
        )

    if not verify_api_access(api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide"
        )

    return api_key


def verify_api_access(api_key: str) -> bool:
    """Validate the API key against the allowed list."""
    if not API_KEY_REQUIRED:
        return True

    if not api_key:
        logger.warning("Tentative d'authentification avec une clé vide")
        return False

    is_valid = api_key in API_KEYS
    if is_valid:
        user = next((name for name, key in API_KEYS_MAPPING.items() if key == api_key), "utilisateur inconnu")
        logger.info(f"Authentification API réussie pour {user}")
    else:
        logger.warning(f"Clé API invalide utilisée : {api_key[:8]}***")

    return is_valid
