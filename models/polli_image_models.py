import aiohttp
import logging
import urllib.parse
from utils.langs import get_translation
import random

logger = logging.getLogger('AlpaLLM')

async def generate_image(prompt, model="flux", seed=None, width=1024, height=1024, nologo=True, private=False, enhance=False, safe=True):
    try:
        params = {
            "prompt": prompt,
            "model": model,
            "width": width,
            "height": height,
            "nologo": str(nologo).lower(),
            "private": str(private).lower(),
            "enhance": str(enhance).lower(),
            "safe": str(safe).lower()
        }
        if seed is not None:
            params["seed"] = seed
        elif seed is None:
            params["seed"] = random.randint(0, 1000000)

        logger.debug(f"Paramètres de la requête : {params}")

        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
        url += "?" + urllib.parse.urlencode(params)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    logger.debug(f"Image générée avec succès pour le prompt : {prompt}")
                    return await response.read()
                else:
                    logger.error(f"Erreur lors de la génération de l'image. Statut : {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'image : {e}")
        return None
