import requests
import logging
import json
from utils.langs import get_translation
import asyncio
from utils.ai_utils import load_preprompt

logger = logging.getLogger('AlphaLLM')

async def gemini(prompt):
    preprompt = load_preprompt()
    
    data = {
        "messages": [
            {"role": "system", "content": preprompt},
            {"role": "user", "content": prompt}
        ],
        "model": 'gemini'
    }
    
    
    try:
        response = requests.post('https://text.pollinations.ai/', json=data)
        if response.status_code == 200:
            if response.headers.get('Content-Type') == 'application/json':
                data = response.json()
            else:
                data = response.text
            logger.info("Réponse générée par Gemini")
            return data
        else:
            logger.error(f"Erreur lors de la requête POST: {response.status_code} - {response.text}")
            return f"Erreur {response.status_code}"
    except Exception as e:
        logger.error(f"Erreur lors de la génération de texte: {e}")
        return f"Une erreur s'est produite: {str(e)}"

