import asyncio
import aiohttp
from bs4 import BeautifulSoup
from markdownify import markdownify

async def fetch_markdown(session, url):
    async with session.get(url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        body = soup.body
        markdown = markdownify(str(body), heading_style="ATX")
        return url, markdown

async def crawl(url):
    async with aiohttp.ClientSession() as session:
        page = await fetch_markdown(session, url)
        return page
