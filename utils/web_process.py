import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import Optional

logger = logging.getLogger("AlphaLLM")

async def get_text_from_url(url: str) -> Optional[str]:
    """Récupérer le texte d'une URL"""
    async with WebProcessor() as processor:
        html = await processor.crawl_website(url)
        if html:
            text = await processor.extract_text(html)
            return await processor.smart_truncate(text)
    return None

class WebProcessor:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.headers = {
            "User-Agent": "AlphaLLMBot/3.0 (HTTP-only)"
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.session.close()
        
    async def crawl_website(self, url: str) -> Optional[str]:
        """Crawling HTTP simple sans JavaScript"""
        try:
            async with self.session.get(
                url, 
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    return await response.text()
                logger.warning(f"Statut HTTP {response.status} pour {url}")
                return None
        except Exception as e:
            logger.error(f"Erreur HTTP: {str(e)}")
            return None

    async def extract_text(self, html: str) -> Optional[str]:
        """Extraction de texte avec BeautifulSoup"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Suppression des éléments indésirables
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript']):
                element.decompose()
                
            # Extraction du texte principal
            text = soup.get_text(separator='\n', strip=True)
            return ' '.join(text.split())  # Normalisation des espaces
        except Exception as e:
            logger.error(f"Erreur d'extraction: {str(e)}")
            return None

    async def smart_truncate(self, text: str, max_length: int = 4000) -> str:
        """Troncature intelligente avec recherche de ponctuation"""
        if len(text) <= max_length:
            return text
            
        truncated = text[:max_length]
        last_punct = max(
            truncated.rfind("."),
            truncated.rfind("!"),
            truncated.rfind("?"),
            truncated.rfind("\n")
        )
        
        return truncated[:last_punct+1].strip() + "..." if last_punct != -1 else truncated + "..."
