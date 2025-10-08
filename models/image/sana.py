import litellm
import os
from dotenv import load_dotenv
import base64
import aiohttp
from utils.config import API_ENDPOINTS_IMAGE, MODELS_CONFIG_IMAGE

load_dotenv()
ELECTRONHUB_API_KEY = os.getenv("ELECTRONHUB_API_KEY")

async def generate_sana(prompt: str, size: str = "1024x1024") -> str:
    """Génère une image avec le modèle Sana via ElectronHub"""
    
    image = litellm.image_generation(
        model="openai/sana",
        api_key=ELECTRONHUB_API_KEY,
        api_base="https://api.electronhub.ai/v1/",
        size=size,
        prompt=prompt                
    )
    
    # Télécharger l'image depuis l'URL et la convertir en base64
    async with aiohttp.ClientSession() as session:
        async with session.get(image.data[0].url) as response:
            if response.status == 200:
                image_data = await response.read()
                return base64.b64encode(image_data).decode('utf-8')
            else:
                raise Exception(f"Erreur lors du téléchargement de l'image: {response.status}")