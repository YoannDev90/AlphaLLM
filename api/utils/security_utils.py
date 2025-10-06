"""
Utilitaires de sécurité
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
import logging

from utils.config import API_KEYS, API_KEY_REQUIRED, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

bearer_scheme = HTTPBearer(
    scheme_name="API Key",
    description="Entrez votre clé API",
    bearerFormat="API Key"
)

def get_api_key(request: Request) -> Optional[str]:
    """
    Extrait la clé API depuis les headers ou les paramètres de requête
    """
    client_ip = request.client.host if request.client else 'unknown'
    logger.debug(f"Tentative d'authentification depuis {client_ip}")
    
    if not API_KEY_REQUIRED:
        logger.debug("Authentification API désactivée, accès autorisé")
        return None
    
    # Essayer d'abord le header X-API-Key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        logger.debug(f"Clé API trouvée dans le header X-API-Key depuis {client_ip}")
        return api_key
    
    # Puis le header Authorization: Bearer <key>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        logger.debug(f"Clé API trouvée dans le header Authorization depuis {client_ip}")
        return auth_header[7:]
    
    # Enfin le paramètre de requête api_key
    api_key = request.query_params.get("api_key")
    if api_key:
        logger.debug(f"Clé API trouvée dans les paramètres de requête depuis {client_ip}")
        return api_key
    
    # Si aucune clé trouvée et qu'elle est requise
    if API_KEY_REQUIRED:
        logger.warning(f"Tentative d'accès sans clé API depuis {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API requise. Utilisez X-API-Key header, Authorization: Bearer <key>, ou paramètre ?api_key=<key>"
        )
    
    return None

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
        logger.info(f"Authentification réussie pour la clé API: {api_key[:8]}***")
    else:
        logger.warning(f"Tentative d'authentification échouée avec la clé API: {api_key[:8]}***")
    
    return is_valid