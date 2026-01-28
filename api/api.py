import asyncio
import logging

import uvicorn

from api.api_utils.app_config import create_app
from api.api_utils.server_utils import get_public_ip, ping_https_server
from api.endpoints import (
    auto_enhance,
    conv_name,
    enhance,
    gen_restore,
    image_edit,
    image_gen,
    image_models,
    improve,
    main,
    remove_bg,
    resources,
    status,
    summarize,
    text_gen,
    text_models,
    upscale,
)
from config import (
    API_HOST,
    API_PORT,
    API_SSL_CERTFILE,
    API_SSL_KEYFILE,
    API_URL,
    LOGGER_NAME,
)

logger = logging.getLogger(LOGGER_NAME)

app = create_app()
app.include_router(main.router)
app.include_router(text_gen.router)
app.include_router(status.router)
app.include_router(conv_name.router)
app.include_router(summarize.router)
app.include_router(resources.router)
app.include_router(text_models.router)
app.include_router(image_models.router)
app.include_router(image_edit.router)
app.include_router(image_gen.router)
app.include_router(improve.router)
app.include_router(enhance.router)
app.include_router(auto_enhance.router)
app.include_router(upscale.router)
app.include_router(gen_restore.router)
app.include_router(remove_bg.router)


async def start_api_async():
    logger.info("Starting API server...")
    try:
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
            app=app, host=API_HOST, port=API_PORT, log_level="critical", access_log=False
        )
        server = uvicorn.Server(config)
        public_ip = await get_public_ip()
        logger.info(f"API running on http://{public_ip}:{API_PORT}")
        asyncio.create_task(ping_https_server(API_URL))
        await server.serve()
    except Exception as e:
        logger.error(f"API server failed: {type(e).__name__}: {e}")
        raise
