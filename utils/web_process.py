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

async def crawl(urls):
    results = {}
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_markdown(session, url) for url in urls]
        pages = await asyncio.gather(*tasks)
        for url, markdown in pages:
            results[url] = markdown
    return results

# Exemple d'utilisation :
if __name__ == "__main__":
    urls = [
        "https://www.example.com",
        "https://www.python.org"
    ]
    results = asyncio.run(crawl(urls))
    for url, md_content in results.items():
        print(f"URL: {url}\nMarkdown:\n{md_content}\n---\n")
