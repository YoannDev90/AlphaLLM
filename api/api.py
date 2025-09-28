import uvicorn
import asyncio
import logging

from api.utils.app_config import create_app
from api.utils.server_utils import get_server_ip
from api.endpoints import main, text_generation, image_generation, info
from utils.config import API_HOST, API_PORT, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

app = create_app()

app.include_router(main.router)
app.include_router(text_generation.router)
app.include_router(image_generation.router)
app.include_router(info.router)

async def start_api_async(host: str = API_HOST, port: int = API_PORT):
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
    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        log_level="info",
        reload=True
    )