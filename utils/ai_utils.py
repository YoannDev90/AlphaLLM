#ai_utils.py
import base64
import logging
import requests
from utils.langs import get_translation

logger = logging.getLogger('AlphaLLM')


def load_preprompt():
    with open('config/preprompt.txt', 'r') as file:
        preprompt = file.read()
    return preprompt

def prompt_test():
    return "Answer \"online\" if you are online"

async def base64convert(image_url):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            mime_type = response.headers.get("Content-Type", "image/jpeg")
            encoded_image = f"data:{mime_type};base64," + base64.b64encode(response.content).decode("utf-8")
            return encoded_image
        else:
            logger.error(f"Erreur lors du téléchargement du fichier: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement ou de la conversion du fichier: {e}")
        return None