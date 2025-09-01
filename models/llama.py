import logging
from utils.config import logger_name
from dotenv import load_dotenv
import os
import litellm
from datetime import datetime
from litellm.integrations.opik.opik import OpikLogger
import os

logger = logging.getLogger(logger_name)

load_dotenv()

async def llama_chat(messages, parameters):
    try:
        logger.debug("Démarrage de la requête Llama")
        logger.debug(f"Nombre de messages: {len(messages)}")
        logger.debug(f"Paramètres reçus: {parameters}")
        
        start_time = datetime.now()
        opik_logger = OpikLogger()
        litellm.callbacks = [opik_logger]

        params = {
            "model": "cerebras/llama3.3-70b",
            "api_key": os.getenv("CEREBRAS_API_KEY"),
            "messages": messages
        }
        
        logger.debug(f"Envoi de la requête au modèle: {params['model']}")
        logger.debug(f"Paramètres de la requête: {params}")
        
        response = litellm.completion(**params)

        logger.debug("Réponse reçue de Llama avec succès")

        usage = response.usage.total_tokens
        model = response.model

        response_text = response.choices[0].message.content
        
        logger.debug(f"Tokens utilisés: {usage}")
        logger.debug(f"Modèle utilisé: {model}")
        logger.debug(f"Longueur de la réponse: {len(response_text)} caractères")
        
        end_time = datetime.now()
        elapsed_time = end_time - start_time
        minutes = elapsed_time.seconds // 60
        seconds = elapsed_time.seconds % 60
        milliseconds = elapsed_time.microseconds // 1000
        
        if minutes > 0:
            elapsed_time_str = f"{minutes} minutes, {seconds}.{milliseconds:03d} seconds"
        else:
            elapsed_time_str = f"{seconds}.{milliseconds:03d} seconds"

        response_info = {
            "response": response_text,
            "usage": usage,
            "model": model,
            "elapsed_time": elapsed_time_str
        }

        logger.debug(f"Requête Llama terminée avec succès en {elapsed_time_str}")
        logger.debug(f"Mode raw activé: {parameters['raw']}")

        if parameters["raw"]:
            return response_info
        else:
            return response_info
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à Llama : {e}")
        logger.error(f"Type d'erreur: {type(e).__name__}")
        return {
            "response": f"Erreur lors de l'appel à Llama : {e}",
            "usage": 0,
            "model": "error",
            "elapsed_time": "0 seconds"
        }
