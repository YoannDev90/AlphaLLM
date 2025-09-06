import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.status import get_status
from utils.config import API_HOST, API_PORT, LOGGER_NAME
import asyncio
import logging
import socket
import aiohttp
import random

logger = logging.getLogger(LOGGER_NAME)

app = FastAPI(
    title="AlphaLLM API",
    description="API pour le projet AlphaLLM",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """Point d'entrée principal de l'API"""
    try:
        https_api = "running" if await is_https_api_running() else "stopped"
        return {"message": "AlphaLLM API", "version": "1.0.0", "HTTP": "running", "HTTPS": https_api}
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de la racine : {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/status")
async def status_check():
    """Point de contrôle de statut de l'API"""
    try:
        status = get_status()
        return status
    except Exception as e:
        logger.error(f"Erreur lors du point de contrôle de statut : {str(e)}")
        return {"status": "error", "message": str(e)}

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

def get_server_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

async def is_https_api_running():
    """Vérifie si l'API HTTPS est en cours d'exécution"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://alphallm-api.onrender.com/status", timeout=30) as response:
                return response.status == 200
    except Exception:
        return False

async def ping_https_server(url: str, interval_range: tuple = (30, 300)):
    """
    Envoie des requêtes ping à un serveur HTTPS à intervalles aléatoires
    
    Args:
        url (str): L'URL du serveur à pinger
        interval_range (tuple): Plage d'intervalles en secondes (min, max)
    """
    min_interval, max_interval = interval_range
    
    if min_interval < 30 or max_interval > 300 or min_interval >= max_interval:
        return
        
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(url, timeout=30) as response:
                    end_time = asyncio.get_event_loop().time()
                    ping_time = (end_time - start_time) * 1000
                    
                    if response.status != 200:
                        logger.warning(f"Ping vers {url} - Status: {response.status} - {ping_time:.2f}ms")
                        
        except asyncio.TimeoutError:
            logger.error(f"Ping vers {url} - Timeout")
        except Exception as e:
            logger.error(f"Ping vers {url} - Erreur: {str(e)}")
        
        next_interval = random.randint(min_interval, max_interval)
        logger.debug(f"Prochain ping dans {next_interval}s")
        await asyncio.sleep(next_interval)