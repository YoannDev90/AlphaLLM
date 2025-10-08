"""
Utilitaires pour le serveur
"""

import aiohttp
import asyncio
import random
import socket
import logging

from utils.config import REQUEST_TIMEOUT, LOGGER_NAME, API_URL

logger = logging.getLogger(LOGGER_NAME)

def get_server_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            logger.debug(f"IP du serveur détectée: {ip}")
            return ip
    except Exception as e:
        logger.warning(f"Impossible de détecter l'IP du serveur, utilisation de localhost: {str(e)}")
        return "127.0.0.1"

async def is_https_api_running():
    url = f"{API_URL}/status"
    try:
        logger.debug(f"Vérification de l'état de l'API HTTPS: {url}")
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                is_running = response.status == 200
                logger.debug(f"API HTTPS {'en fonctionnement' if is_running else 'arrêtée'} (status: {response.status})")
                return is_running
    except Exception as e:
        logger.warning(f"Erreur lors de la vérification de l'API HTTPS: {str(e)}")
        return False

async def ping_https_server(url: str, interval_range: tuple = (30, 300)):
    min_interval, max_interval = interval_range
    
    if min_interval < 30 or max_interval > 300 or min_interval >= max_interval:
        logger.error(f"Paramètres d'intervalle invalides: {interval_range}. Min=30s, Max=300s")
        return
            
    while True:
        try:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(url) as response:
                    end_time = asyncio.get_event_loop().time()
                    ping_time = (end_time - start_time) * 1000
                    
                    if response.status == 200:
                        logger.debug(f"Ping vers {url} - OK - {ping_time:.2f}ms")
                    else:
                        logger.warning(f"Ping vers {url} - Status: {response.status} - {ping_time:.2f}ms")
                        
        except asyncio.TimeoutError:
            logger.error(f"Ping vers {url} - Timeout après {REQUEST_TIMEOUT}s")
        except Exception as e:
            logger.error(f"Ping vers {url} - Erreur: {str(e)}")
        
        next_interval = random.randint(min_interval, max_interval)
        logger.debug(f"Prochain ping dans {next_interval}s")
        await asyncio.sleep(next_interval)