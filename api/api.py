import logging

import uvicorn

from api.api_utils.app_config import create_app
from api.api_utils.server_utils import get_public_ip
#from api.endpoints import image_gen, main, text_gen, info, misc, image_edit
from api.endpoints import info, main, misc, text_gen
from config import API_HOST, LOGGER_NAME, API_PORT, API_SSL_CERTFILE, API_SSL_KEYFILE

logger = logging.getLogger(LOGGER_NAME)

app = create_app()
app.include_router(main.router)
app.include_router(info.router)
# app.include_router(image_gen.router)
# app.include_router(image_edit.router)
app.include_router(text_gen.router)
app.include_router(misc.router)

async def start_api_async():
    # config = uvicorn.Config(
    #     app=app,
    #     host=API_HOST,
    #     port=API_PORT,
    #     log_level="critical",
    #     access_log=False,
    #     ssl_certfile=API_SSL_CERTFILE,
    #     ssl_keyfile=API_SSL_KEYFILE,
    # )
    config = uvicorn.Config(
        app=app,
        host=API_HOST,
        port=API_PORT,
        log_level="critical",
        access_log=False
    )
    server = uvicorn.Server(config)
    public_ip = await get_public_ip()
    logger.info(f"API running on http://{public_ip}:{API_PORT}")
    await server.serve()