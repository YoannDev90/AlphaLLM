import uvicorn
import logging
from api.api_utils.app_config import create_app
from api.api_utils.server_utils import get_public_ip
#from api.endpoints import image_gen, main, text_gen, info, misc, image_edit
from api.endpoints import text_gen, info, misc, main
from config import LOGGER_NAME, HOST, PORT, SSL_CERTFILE, SSL_KEYFILE

logger = logging.getLogger(LOGGER_NAME)

app = create_app()

logger.info("Configuring API routers")
app.include_router(main.router)
app.include_router(info.router)
# app.include_router(image_gen.router)
# app.include_router(image_edit.router)
app.include_router(text_gen.router)
app.include_router(misc.router)
logger.info("API routers configured")

async def start_api_async():
    target_host = HOST
    target_port = PORT
    cert_file = SSL_CERTFILE
    key_file = SSL_KEYFILE
    # config = uvicorn.Config(
    #     app=app,
    #     host=target_host,
    #     port=target_port,
    #     log_level="error",
    #     access_log=False,
    #     ssl_certfile=cert_file,
    #     ssl_keyfile=key_file,
    # )
    config = uvicorn.Config(
        app=app,
        host=target_host,
        port=target_port,
        log_level="error",
        access_log=False
    )
    server = uvicorn.Server(config)
    public_ip = await get_public_ip()
    logger.info(f"API running on http://{public_ip}:{target_port}")
    await server.serve()