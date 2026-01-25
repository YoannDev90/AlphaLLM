"""Utility helpers for monitoring and pinging the API server."""

import asyncio
import logging
import random

import aiohttp

from config import API_URL, LOGGER_NAME, API_REQUEST_TIMEOUT

logger = logging.getLogger(LOGGER_NAME)

async def get_public_ip():
    url = "https://api.ipify.org?format=text"
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    ip = await response.text()
                    logger.debug(f"Adresse IP publique récupérée: {ip}")
                    return ip.strip()
                else:
                    logger.warning(f"Échec de la récupération de l'IP publique, status: {response.status}")
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération de l'IP publique: {str(e)}")
    return None

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
            timeout = aiohttp.ClientTimeout(total=API_REQUEST_TIMEOUT)
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
            logger.error(f"Ping vers {url} - Timeout après {API_REQUEST_TIMEOUT}s")
        except Exception as e:
            logger.error(f"Ping vers {url} - Erreur: {str(e)}")
        
        next_interval = random.randint(min_interval, max_interval)
        await asyncio.sleep(next_interval)