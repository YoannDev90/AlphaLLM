"""
Utilitaires de sécurité
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
import logging

from utils.config import API_KEYS, API_KEYS_MAPPING, API_KEY_REQUIRED, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

bearer_scheme = HTTPBearer(
    scheme_name="API Key",
    description="Entrez votre clé API",
    bearerFormat="API Key"
)

def get_api_key(request: Request) -> Optional[str]:
    """
    Extrait la clé API depuis les headers ou les paramètres de requête et la valide
    """
    client_ip = request.client.host if request.client else 'unknown'
    
    if not API_KEY_REQUIRED:
        return None
    
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
    
    if not api_key:
        api_key = request.query_params.get("api_key")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API requise. Utilisez X-API-Key header, Authorization: Bearer <key>, ou paramètre ?api_key=<key>"
        )
    
    # Vérifier que la clé API est valide
    if not verify_api_access(api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide"
        )
    
    return api_key

def verify_api_access(api_key: str) -> bool:
    """
    Vérifie si la clé API est valide
    """
    if not API_KEY_REQUIRED:
        logger.debug("Authentification API désactivée, accès accordé")
        return True
    
    if not api_key:
        logger.warning("Tentative de vérification avec une clé API vide")
        return False
    
    is_valid = api_key in API_KEYS
    if is_valid:
        user_name = next((name for name, key in API_KEYS_MAPPING.items() if key == api_key), "utilisateur inconnu")
        logger.info(f"Authentification réussie pour l'utilisateur: {user_name}")
    else:
        logger.warning(f"Tentative d'authentification échouée avec la clé API: {api_key[:8]}***")
    
    return is_valid