from cerebras.cloud.sdk import Cerebras
import logging
from dotenv import load_dotenv
import os
from datetime import datetime

logger = logging.getLogger('AlphaLLM')

load_dotenv()

cerebras_client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"),max_retries=3)

def load_preprompt() -> str:
    """Charge le pré-prompt depuis un fichier"""
    try:
        with open("config/preprompt.txt", "r", encoding="utf-8") as file:
            preprompt = file.read()
        logger.debug("Preprompt loaded successfully")
        now = datetime.now()
        preprompt += f"\nDate: {now.strftime('%Y-%m-%d')}\nHour: CEST {now.strftime('%H:%M:%S')}\n"
        return preprompt
    except Exception as e:
        logger.error(f"Error loading preprompt: {str(e)}")
        raise

async def chat(user_message, perso_preprompt, parameters):
    try:
        if parameters.get("preprompt", True):
            preprompt = load_preprompt()
            if perso_preprompt:
                preprompt += f"\n{perso_preprompt}"
        else:
            preprompt = ""

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
