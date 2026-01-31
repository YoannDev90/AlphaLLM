"""
Configuration de l'application FastAPI pour AlphaLLM
"""

import json
import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import (API_BAN_THRESHOLD, API_KEY_REQUIRED, API_KEYS,
                    API_RATE_LIMIT, LOGGER_NAME)

logger = logging.getLogger(LOGGER_NAME)

# In-memory storage for rate limiting and banning
request_counts: Dict[str, list] = defaultdict(list)
failed_counts: Dict[str, int] = defaultdict(int)
banned_ips: set = set()

# File for persistence
BAN_DATA_FILE = Path("data/ban_data.json")

security = HTTPBearer(auto_error=False)


def load_ban_data():
    """Load banned IPs and failed counts from file."""
    global banned_ips, failed_counts
    if BAN_DATA_FILE.exists():
        try:
            with open(BAN_DATA_FILE, "r") as f:
                data = json.load(f)
                banned_ips = set(data.get("banned_ips", []))
                failed_counts = defaultdict(int, data.get("failed_counts", {}))
            logger.info(f"Loaded ban data: {len(banned_ips)} banned IPs")
        except Exception as e:
            logger.error(f"Failed to load ban data: {e}")


def save_ban_data():
    """Save banned IPs and failed counts to file."""
    try:
        data = {
            "banned_ips": list(banned_ips),
            "failed_counts": dict(failed_counts),
        }
        BAN_DATA_FILE.parent.mkdir(exist_ok=True)
        with open(BAN_DATA_FILE, "w") as f:
            json.dump(data, f)
        logger.debug("Saved ban data")
    except Exception as e:
        logger.error(f"Failed to save ban data: {e}")


def save_api_keys():
    """Save API keys to file."""
    from config import API_KEYS, API_KEYS_FILE

    try:
        Path(API_KEYS_FILE).parent.mkdir(exist_ok=True)
        with open(API_KEYS_FILE, "w") as f:
            json.dump(API_KEYS, f)
        logger.debug("Saved API keys")
    except Exception as e:
        logger.error(f"Failed to save API keys: {e}")


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Verify API key if required."""
    if not API_KEY_REQUIRED:
        return None
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")

    key_data = API_KEYS.get(credentials.credentials)
    if not key_data:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Check expiration
    expires = key_data.get("expires")
    if expires:
        from datetime import datetime

        if datetime.now() > datetime.fromisoformat(expires):
            raise HTTPException(status_code=401, detail="API key expired")

    # Check rate limit (per key)
    rate_limit = key_data.get("rate_limit", float("inf"))
    requests_used = key_data.get("requests_used", 0)
    if requests_used >= rate_limit:
        raise HTTPException(status_code=429, detail="API key rate limit exceeded")

    # Increment usage
    key_data["requests_used"] = requests_used + 1
    # Save updated keys
    save_api_keys()

    return credentials.credentials


def create_app() -> FastAPI:
    logger.info("Initialisation de l'application FastAPI")

    # Load ban data on startup
    load_ban_data()

    app = FastAPI(
        title="AlphaLLM API",
        description="API pour le projet AlphaLLM",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    logger.debug("Application FastAPI initialisée avec succès")

    logger.info("Configuration des middlewares")

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    logger.debug("Middleware TrustedHost configuré")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    logger.debug("Middleware CORS configuré")

    # Add rate limiting and ban middleware
    @app.middleware("http")
    async def rate_limit_and_ban_middleware(request: Request, call_next):
        client_ip = request.client.host

        # Check if IP is banned
        if client_ip in banned_ips:
            logger.warning(f"Banned IP {client_ip} tried to access")
            return Response(content="Forbidden", status_code=403)

        current_time = time.time()

        # Clean old requests (older than 1 minute)
        request_counts[client_ip] = [
            t for t in request_counts[client_ip] if current_time - t < 60
        ]

        # Check rate limit
        if len(request_counts[client_ip]) >= API_RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for IP {client_ip}")
            return Response(content="Too Many Requests", status_code=429)

        # Add current request
        request_counts[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # If response is error (4xx or 5xx), increment failed count
        if response.status_code >= 400:
            failed_counts[client_ip] += 1
            if failed_counts[client_ip] >= API_BAN_THRESHOLD:
                banned_ips.add(client_ip)
                logger.warning(f"IP {client_ip} banned due to too many failures")
                save_ban_data()  # Save after banning
        else:
            # Reset failed count on success
            if client_ip in failed_counts:
                failed_counts[client_ip] = 0

        return response

    logger.debug("Middleware rate limiting et ban configuré")

    app.openapi = lambda: custom_openapi(app)
    logger.debug("Schema OpenAPI personnalisé configuré")

    logger.info("Application FastAPI complètement configurée")
    return app


def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title="AlphaLLM API",
        version="2.0.0",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": "Entrez votre clé API dans le champ ci-dessous",
        }
    }

    openapi_schema["security"] = [{"APIKeyAuth": []}]

    if "paths" in openapi_schema:
        for path, path_obj in openapi_schema["paths"].items():
            if "/generate/" in path or path in ["/summarize", "/conv_name"]:
                for method, method_obj in path_obj.items():
                    if method.lower() in ["get", "post", "put", "delete"]:
                        method_obj["security"] = [{"APIKeyAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema
