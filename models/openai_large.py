import requests
import logging
import json
import asyncio
from utils.langs import get_translation
from utils.ai_utils import load_preprompt

logger = logging.getLogger('AlphaLLM')

async def openai_large(prompt, images=None):
    preprompt = load_preprompt()
    
    data = {
        "messages": [
            {"role": "system", "content": preprompt}
        ],
        "model": 'openai-large'
    }
    
    if images!=None:
        user_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
            ]
        }
        for image_url in images:
            user_message["content"].append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        data["messages"].append(user_message)
    else:
        data["messages"].append({"role": "user", "content": prompt})
    
    try:
        response = requests.post('https://text.pollinations.ai/', json=data)
        if response.status_code == 200:
            if response.headers.get('Content-Type') == 'application/json':
                data = response.json()
            else:
                data = response.text
            logger.info("Réponse générée par OpenAI Large")
            return data
        else:
            logger.error(f"Erreur lors de la requête POST: {response.status_code} - {response.text}")
            return f"Erreur {response.status_code}: {response.text}"
    except Exception as e:
        logger.error(f"Erreur lors de la génération de texte: {e}")
        return f"Une erreur s'est produite: {str(e)}"

