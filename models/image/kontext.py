import os
from dotenv import load_dotenv
import base64
import aiohttp
import urllib.parse
import random

load_dotenv()
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

async def generate_kontext(prompt: str, size: str = "1024x1024") -> str:
    """
    Génère une image avec le modèle Kontext via Pollinations

    Args:
        prompt: Le prompt pour générer l'image
        size: La taille de l'image (par défaut "1024x1024")
        
    Returns:
        L'image encodée en base64
    """
    width, height = map(int, size.split("x"))
    
    params = {
        "prompt": prompt,
        "model": "kontext",
        "width": width,
        "height": height,
        "seed": random.randint(0, 2**31 - 1),
        "nologo": "true",
        "private": "true",
        "enhance": "false",
        "safe": "false",
        "token": POLLINATIONS_API_KEY
    }

    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
    url += "?" + urllib.parse.urlencode(params)

    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            if response.status == 200:
                image_data = await response.read()
                return base64.b64encode(image_data).decode('utf-8')
            else:
                error_message = await response.text()
                raise Exception(f"Erreur lors de la génération de l'image. Status: {response.status} - {error_message}")
