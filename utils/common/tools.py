from tavily import TavilyClient
import os
from dotenv import load_dotenv
import asyncio
import logging
from utils.config.app_config import LOGGER_NAME

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

logger = logging.getLogger(LOGGER_NAME)

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

async def search_internet_tool(query):
    try:
        response = tavily_client.search(query)
        return response
    except Exception as e:
        logger.error(f"Error during internet search: {e}")
        return "An error occurred while searching the internet."