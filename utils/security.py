"""
Module de sécurité pour l'API AlphaLLM
Gère l'authentification par clé API et le rate limiting
"""
import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict, deque
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.config import API_KEYS, MAX_REQUESTS_PER_MINUTE, API_KEY_REQUIRED
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Gestionnaire de limitation de taux pour prévenir le DDoS"""
    
    def __init__(self, max_requests: int = MAX_REQUESTS_PER_MINUTE, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Dictionnaire des timestamps des requêtes par clé API/IP
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
        self._cleanup_task = None
        self._initialized = False
    
    def _ensure_cleanup_started(self):
        """S'assure que la tâche de nettoyage est démarrée (avec loop en cours)"""
        if not self._initialized:
            try:
                if self._cleanup_task is None or self._cleanup_task.done():
                    self._cleanup_task = asyncio.create_task(self._cleanup_old_requests())
                self._initialized = True
            except RuntimeError:
                # Pas de loop en cours, la tâche sera créée plus tard
                pass
    
    async def _cleanup_old_requests(self):
        """Nettoie les anciennes requêtes périodiquement"""
        while True:
            try:
                current_time = time.time()
                cutoff_time = current_time - self.window_seconds
                
                # Nettoie les anciennes entrées
                for key, timestamps in list(self.requests.items()):
                    while timestamps and timestamps[0] < cutoff_time:
                        timestamps.popleft()
                    
                    # Supprime les clés vides
                    if not timestamps:
                        del self.requests[key]
                
                await asyncio.sleep(30)  # Nettoyage toutes les 30 secondes
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage du rate limiter: {e}")
                await asyncio.sleep(60)
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Vérifie si une requête est autorisée pour un identifiant donné
        
        Args:
            identifier: Clé API ou adresse IP
            
        Returns:
            True si la requête est autorisée, False sinon
        """
        # S'assure que le nettoyage automatique est démarré
        self._ensure_cleanup_started()
        
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        # Nettoie les anciennes requêtes pour cet identifiant
        timestamps = self.requests[identifier]
        while timestamps and timestamps[0] < cutoff_time:
            timestamps.popleft()
        
        # Vérifie si la limite est atteinte
        if len(timestamps) >= self.max_requests:
            return False
        
        # Enregistre cette requête
        timestamps.append(current_time)
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Retourne le nombre de requêtes restantes pour un identifiant"""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        timestamps = self.requests[identifier]
        # Compte seulement les requêtes récentes
        recent_requests = sum(1 for ts in timestamps if ts > cutoff_time)
        return max(0, self.max_requests - recent_requests)

class APIKeyAuth(HTTPBearer):
    """Gestionnaire d'authentification par clé API"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.rate_limiter = RateLimiter()
    
    async def __call__(self, request: Request) -> Optional[str]:
        """
        Vérifie l'authentification et le rate limiting
        
        Returns:
            La clé API si valide, None si l'authentification n'est pas requise
        """
        # Si l'authentification n'est pas requise, utilise l'IP pour le rate limiting
        if not API_KEY_REQUIRED:
            client_ip = self._get_client_ip(request)
            if not self.rate_limiter.is_allowed(client_ip):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Trop de requêtes. Limite: {MAX_REQUESTS_PER_MINUTE} par minute"
                )
            return None
        
        # Obtient la clé API depuis l'header Authorization
        api_key = self._extract_api_key(request)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clé API requise. Utilisez l'header Authorization: Bearer <votre-clé>"
            )
        
        # Vérifie si la clé API est valide
        if api_key not in API_KEYS:
            logger.warning(f"Tentative d'accès avec une clé API invalide: {api_key[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clé API invalide"
            )
        
        # Vérifie le rate limiting pour cette clé API
        if not self.rate_limiter.is_allowed(api_key):
            remaining = self.rate_limiter.get_remaining_requests(api_key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de requêtes atteinte. Limite: {MAX_REQUESTS_PER_MINUTE} par minute. "
                       f"Requêtes restantes: {remaining}"
            )
        
        return api_key
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extrait la clé API de la requête"""
        # Essaie d'abord l'header Authorization Bearer
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Retire "Bearer "
        
        # Essaie ensuite le paramètre de requête
        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key
        
        # Essaie l'header X-API-Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtient l'adresse IP du client"""
        # Vérifie les headers de proxy en premier
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Utilise l'IP directe si aucun proxy
        return request.client.host if request.client else "unknown"

# Instance globale du gestionnaire d'authentification
api_auth = APIKeyAuth()

async def get_api_key(request: Request) -> Optional[str]:
    """Fonction helper pour obtenir la clé API authentifiée"""
    return await api_auth(request)

def verify_api_access(api_key: Optional[str] = None) -> bool:
    """Vérifie si l'accès à l'API est autorisé"""
    if not API_KEY_REQUIRED:
        return True
    return api_key is not None and api_key in API_KEYS