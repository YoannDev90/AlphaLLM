import os
from dotenv import load_dotenv
import base64
import aiohttp
import urllib.parse
import random
import asyncio
from pathlib import Path

load_dotenv()
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

async def generate_seedream(prompt: str, size: str = "1024x1024") -> str:
    """
    Génère une image avec le modèle Seedream via Pollinations

    Args:
        prompt: Le prompt pour générer l'image
        size: La taille de l'image (par défaut "1024x1024")
        
    Returns:
        L'image encodée en base64
    """
    width, height = map(int, size.split("x"))
    
    params = {
        "prompt": prompt,
        "model": "seedream",
        "width": width,
        "height": height,
        "seed": random.randint(0, 2**31 - 1),
        "nologo": "true",
        "private": "true",
        "nofeed": "true",
        "enhance": "false",
        "safe": "false"
    }

    url = f"https://enter.pollinations.ai/api/generate/image/{urllib.parse.quote(prompt)}"
    url += "?" + urllib.parse.urlencode(params)
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            if response.status == 200:
                image_data = await response.read()
                return base64.b64encode(image_data).decode('utf-8')
            else:
                error_message = await response.text()
                raise Exception(f"Erreur lors de la génération de l'image. Status: {response.status} - {error_message}")


if __name__ == "__main__":
    prompt = input("Enter prompt (default: 'A steampunk airship in the clouds'): ").strip() or "A steampunk airship in the clouds"
    size = input("Enter size (default: '1024x1024'): ").strip() or "1024x1024"
    
    print(f"Generating image with prompt: '{prompt}'")
    print(f"Size: {size}")
    
    try:
        result = asyncio.run(generate_seedream(prompt, size))
        print(f"✓ Image generated successfully!")
        print(f"Base64 length: {len(result)} characters")
        
        # Save the image
        output_dir = Path(__file__).parent.parent.parent / "generated_images"
        output_dir.mkdir(exist_ok=True)
        
        image_bytes = base64.b64decode(result)
        image_filename = output_dir / "seedream_output.png"
        with open(image_filename, "wb") as f:
            f.write(image_bytes)
        
        print(f"✓ Image saved to: {image_filename}")
    except Exception as e:
        print(f"✗ Error: {e}")
