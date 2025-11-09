import litellm
import os
from dotenv import load_dotenv
import base64
import aiohttp
import asyncio
from pathlib import Path

load_dotenv()
NAVY_API_KEY = os.getenv("NAVY_API_KEY")

async def generate_qwen(prompt: str, size: str = "1024x1024") -> str:
    """
    Génère une image avec le modèle Qwen Image
    
    Args:
        prompt: Le prompt pour générer l'image
        size: La taille de l'image (par défaut "1024x1024")
        
    Returns:
        L'image encodée en base64
    """
    image = litellm.image_generation(
        model="openai/qwen-image",
        api_key=NAVY_API_KEY,
        api_base="https://api.navy/v1/",
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


if __name__ == "__main__":
    prompt = input("Enter prompt (default: 'An ancient temple in the jungle'): ").strip() or "An ancient temple in the jungle"
    size = input("Enter size (default: '1024x1024'): ").strip() or "1024x1024"
    
    print(f"Generating image with prompt: '{prompt}'")
    print(f"Size: {size}")
    
    try:
        result = asyncio.run(generate_qwen(prompt, size))
        print(f"✓ Image generated successfully!")
        print(f"Base64 length: {len(result)} characters")
        
        # Save the image
        output_dir = Path(__file__).parent.parent.parent / "generated_images"
        output_dir.mkdir(exist_ok=True)
        
        image_bytes = base64.b64decode(result)
        image_filename = output_dir / "qwenimage_output.png"
        with open(image_filename, "wb") as f:
            f.write(image_bytes)
        
        print(f"✓ Image saved to: {image_filename}")
    except Exception as e:
        print(f"✗ Error: {e}")
