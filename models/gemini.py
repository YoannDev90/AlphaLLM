from google import genai
import logging
from dotenv import load_dotenv
import os
import json
import asyncio

logger = logging.getLogger('AlphaLLM')

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

async def gemini_chat(user_message, preprompt, tools, bot, user, parameters):
        try:
            response = await gemini_client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_message]
            )

            return response.text

        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse Gemini : {e}")
            return f"Erreur lors de la génération de la réponse : {e}"