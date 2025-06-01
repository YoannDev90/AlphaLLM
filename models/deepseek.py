import aiohttp
import logging
from dotenv import load_dotenv
import os
import json

logger = logging.getLogger('AlphaLLM')

load_dotenv()

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

async def deepseek_chat(user_message, preprompt, tools, bot, user, parameters):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "deepseek/deepseek-r1:free",
                "messages": [
                    {
                        "role": "system",
                        "content": preprompt
                    },
                    {
                        "role": "user", 
                        "content": user_message
                    }
                ],
            }

            async with session.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_msg = await response.text()
                    logger.error(f"API Error {response.status}: {error_msg}")
                    return f"Erreur API: {error_msg}"

                response_json = await response.json()
                message_data = response_json['choices'][0]['message']
                
                return message_data.get('content')

    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse : {e}")
        return f"Erreur critique : {str(e)}"
