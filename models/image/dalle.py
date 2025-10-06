import litellm
import os
from dotenv import load_dotenv
import base64
import aiohttp

load_dotenv()
MNNAI_API_KEY = os.getenv("MNN_AI_API_KEY")

async def generate_dalle(prompt: str, size: str = "1024x1024") -> str:
    """
    Génère une image avec le modèle DALL-E 3
    
    Args:
        prompt: Le prompt pour générer l'image
        size: La taille de l'image (par défaut "1024x1024")
        
    Returns:
        L'image encodée en base64
    """
    image = litellm.image_generation(
        model="dall-e-3",
        api_key=MNNAI_API_KEY,
        api_base="https://api.mnnai.ru/v1",
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