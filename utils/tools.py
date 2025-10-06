from tavily import TavilyClient
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

async def search_internet_tool(query):
    try:
        response = tavily_client.search(query)
        return response
    except Exception as e:
        print(f"Error during internet search: {e}")
        return "An error occurred while searching the internet."