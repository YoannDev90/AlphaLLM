"""Utility helpers for monitoring and pinging the API server."""

import asyncio
import logging
import random

import aiohttp

from config import API_REQUEST_TIMEOUT, API_URL, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


async def get_public_ip():
    url = "https://api.ipify.org?format=text"
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    ip = await response.text()
                    logger.debug(f"Public IP address retrieved: {ip}")
                    return ip.strip()
                else:
                    logger.warning(
                        f"Failed to retrieve public IP, " f"status: {response.status}"
                    )
    except Exception as e:
        logger.warning(f"Error retrieving public IP: {str(e)}")
    return None


async def is_https_api_running():
    url = f"{API_URL}/status"
    try:
        logger.debug(f"Checking HTTPS API status: {url}")
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                is_running = response.status == 200
                logger.debug(
                    f"HTTPS API {'running' if is_running else 'stopped'} "
                    f"(status: {response.status})"
                )
                return is_running
    except Exception as e:
        logger.warning(f"Error checking HTTPS API: {str(e)}")
        return False


async def ping_https_server(url: str, interval_range: tuple = (30, 300)):
    min_interval, max_interval = interval_range

    if min_interval < 30 or max_interval > 300 or min_interval >= max_interval:
        logger.error(
            f"Invalid interval parameters: {interval_range}. " f"Min=30s, Max=300s"
        )
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
                        logger.debug(f"Ping to {url} - OK - {ping_time:.2f}ms")
                    else:
                        logger.warning(
                            f"Ping to {url} - Status: {response.status} - {ping_time:.2f}ms"
                        )

        except asyncio.TimeoutError:
            logger.error(f"Ping to {url} - Timeout after {API_REQUEST_TIMEOUT}s")
        except Exception as e:
            logger.error(f"Ping to {url} - Error: {str(e)}")

        next_interval = random.randint(min_interval, max_interval)
        await asyncio.sleep(next_interval)
