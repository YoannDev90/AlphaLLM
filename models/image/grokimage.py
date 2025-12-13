import asyncio
import base64
import os
from pathlib import Path

import aiohttp
import litellm
from dotenv import load_dotenv

load_dotenv()
VOID_API_KEY = os.getenv("VOID_API_KEY")

async def generate_grokimage(prompt: str, size: str = "1024x1024") -> str:
    """
    Génère une image avec le modèle Grok-Image
    
    Args:
        prompt: Le prompt pour générer l'image
        size: La taille de l'image (par défaut "1024x1024")
        
    Returns:
        L'image encodée en base64
    """
    image = litellm.image_generation(
        model="openai/grok-2-image",
        api_key=VOID_API_KEY,
        api_base="https://api.voidai.app/v1",
        #size=size,
        prompt=prompt           
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(image.data[0].url) as response:
            if response.status == 200:
                image_data = await response.read()
                return base64.b64encode(image_data).decode('utf-8')
            else:
                raise Exception(f"Erreur lors du téléchargement de l'image: {response.status}")


if __name__ == "__main__":
    prompt = input("Enter prompt (default: 'A cyberpunk hacker in a neon-lit room with holographic screens'): ").strip() or "A cyberpunk hacker in a neon-lit room with holographic screens"
    size = input("Enter size (default: '1024x1024'): ").strip() or "1024x1024"
    
    print(f"Generating image with prompt: '{prompt}'")
    print(f"Size: {size}")
    
    try:
        result = asyncio.run(generate_grokimage(prompt, size))
        print(f"✓ Image generated successfully!")
        print(f"Base64 length: {len(result)} characters")
        
        # Save the image
        output_dir = Path(__file__).parent.parent.parent / "generated_images"
        output_dir.mkdir(exist_ok=True)
        
        image_bytes = base64.b64decode(result)
        image_filename = output_dir / "grokimage_output.png"
        with open(image_filename, "wb") as f:
            f.write(image_bytes)
        
        print(f"✓ Image saved to: {image_filename}")
    except Exception as e:
        print(f"✗ Error: {e}")