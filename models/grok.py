import aiohttp
import urllib.parse
import json
import asyncio
import logging
from dotenv import load_dotenv
import os

logger = logging.getLogger('AlphaLLM')

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

async def grok_chat(user_message, preprompt, tools, bot, user, parameters):
    encoded_prompt = urllib.parse.quote(user_message)
    url = f"https://text.pollinations.ai/{encoded_prompt}"

    params = {
        "system": preprompt,
        "model": "grok",
        "token": POLLINATIONS_API_KEY,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                response_message = await response.text()

                # from utils.ai_gen import generate_image_tools
        
                # if response_message.tool_calls:
                #     for tool_call in response_message.tool_calls:
                #         if tool_call.function.name == "generate_image_tools":
                #             try:
                #                 args = json.loads(tool_call.function.arguments)
                #                 image_data = await generate_image_tools(
                #                     prompt=args.get("prompt"),
                #                     bot=bot,
                #                     user=user,
                #                     parameters=parameters,
                #                     tool_parameters={
                #                         "size": args.get("size", "1024x1024"),
                #                     }
                #                 )
                #                 return image_data
                #             except json.JSONDecodeError:
                #                 logger.error("Erreur de parsing JSON")
                #             except ValueError as e:
                #                 logger.error(str(e))
                
                return response_message
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse EvilGPT : {e}")
            return f"Erreur lors de la génération de la réponse : {e}"
