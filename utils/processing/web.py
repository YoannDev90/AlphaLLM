import asyncio
import aiohttp
from bs4 import BeautifulSoup
from markdownify import markdownify

async def crawl(url: str) -> str:
    async with aiohttp.ClientSession().get(url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        body = soup.body
        markdown = markdownify(str(body), heading_style="ATX")
        return markdown
