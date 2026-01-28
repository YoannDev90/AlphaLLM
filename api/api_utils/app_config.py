"""
Configuration de l'application FastAPI pour AlphaLLM
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def create_app() -> FastAPI:
    logger.info("Initialisation de l'application FastAPI")

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
