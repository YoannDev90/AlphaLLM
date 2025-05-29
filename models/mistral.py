from mistralai import Mistral
from utils.image_gen import generate_image
import logging
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import aiohttp
from utils.gallery import gallery

logger = logging.getLogger('AlphaLLM')

load_dotenv()

mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

image_generation_tool = {
    "type": "function",
    "function": {
        "name": "generate_image_tools",
        "description": "Generates an image from a text prompt",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string", 
                    "description": "Detailed description in English."
                },
                "size": {
                    "type": "string", 
                    "description": "Image size to generate in pixels (width x height), maximum 2048x2048, minimum 512x512",
                    "examples": ["512x512", "1024x1024", "2048x2048", "2048x1024", "1024x2048"],
                    "default": "1024x1024",
                }
            },
            "required": ["prompt", "size"],
        }
    }
}

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

async def chat(user_message, perso_preprompt, bot, user, parameters):
    try:
        if parameters.get("preprompt", True):
            preprompt = load_preprompt()
            if perso_preprompt:
                preprompt += f"\n{perso_preprompt}"
        else:
            preprompt = ""

        tools = [image_generation_tool] if parameters.get("tools", True) else []

        completion = await mistral_client.chat.completions.create(
            messages=[
                {"role": "system", "content": preprompt},
                {"role": "user", "content": user_message}
            ],
            tools=tools,
            tool_choice="auto" if tools else None,
            model="mistral-small-latest"
        )
        response_message = completion.choices[0].message

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "generate_image_tools":
                    try:
                        args = json.loads(tool_call.function.arguments)
                        image_data = await generate_image_tools(
                            prompt=args.get("prompt"),
                            bot=bot,
                            user=user,
                            parameters=parameters,
                            tool_parameters={
                                "size": args.get("size", "1024x1024"),
                            }
                        )
                        return image_data
                    except json.JSONDecodeError:
                        logger.error("Erreur de parsing JSON")
                    except ValueError as e:
                        logger.error(str(e))
        
        return response_message.content
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse Mistral : {e}")
        return f"Erreur lors de la génération de la réponse : {e}"

async def generate_image_tools(prompt: str, bot, user, parameters, tool_parameters) -> str:
    try:
        if parameters.get("tools", True):
            size = tool_parameters.get("size", "1024x1024")
            width, height = map(int, size.split('x'))
            image_data = await generate_image(
                prompt=prompt,
                width=width,
                height=height
            )
            logger.debug(f"Image générée (prompt:{prompt}, taille: {size})")
            await gallery(bot, image_data, prompt, user)
            return image_data
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'image : {e}")
        return f"Erreur lors de la génération de l'image : {e}"