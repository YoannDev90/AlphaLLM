"""
API principale AlphaLLM - Version modulaire
"""

import uvicorn
import asyncio
import logging

from api.config.app_config import create_app, get_server_ip, ping_https_server
from api.endpoints import main, text_generation, image_generation, info
from utils.config import API_HOST, API_PORT, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

# Crée l'application FastAPI
app = create_app()

# Enregistre les routers des endpoints
app.include_router(main.router)
app.include_router(text_generation.router)
app.include_router(image_generation.router)
app.include_router(info.router)

async def start_api_async(host: str = API_HOST, port: int = API_PORT):
    """
    Version asynchrone pour démarrer l'API dans une boucle d'événements existante
    """
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="error",
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.info(f"API démarrée sur {get_server_ip()}:{port}")
    await server.serve()

if __name__ == "__main__":
    # Démarre l'API en mode standalone
    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        log_level="info",
        reload=True
    )