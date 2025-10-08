import uvicorn
import asyncio
import logging

from api.utils.app_config import create_app
from api.utils.server_utils import get_server_ip
from api.endpoints import image_gen, main, text_gen, info, audio_gen
from utils.config import API_HOST, API_PORT, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

app = create_app()

logger.info("Configuration des routers de l'API")
app.include_router(main.router)
logger.debug("Router 'main' ajouté")
app.include_router(text_gen.router)
logger.debug("Router 'text_generation' ajouté")
app.include_router(image_gen.router)
logger.debug("Router 'image_generation' ajouté")
# app.include_router(audio_gen.router)
# logger.debug("Router 'audio_generation' ajouté")
app.include_router(info.router)
logger.debug("Router 'info' ajouté")
logger.info("Tous les routers ont été configurés avec succès")

async def start_api_async(host: str = API_HOST, port: int = API_PORT):
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="error",
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.info(f"API démarrée sur http://{get_server_ip()}:{port}")
    await server.serve()