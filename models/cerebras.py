from cerebras.cloud.sdk import Cerebras
from utils.langs import get_translation
import logging
from dotenv import load_dotenv
import os
from utils.ai_utils import load_preprompt

logger = logging.getLogger('AlphaLLM')

load_dotenv()

cerebras_client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"),max_retries=3)

async def cerebras(user_message):
    try:
        preprompt = load_preprompt()
        
        completion = cerebras_client.chat.completions.create(
            messages=[
                {"role": "user", "content": user_message},
                {"role": "system", "content": preprompt}
            ],
            model="llama3.3-70b"
        )
        logger.info("Réponse générée par Cerebras")
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse Cerebras : {e}")
        return f"Erreur lors de la génération de la réponse : {e}"
