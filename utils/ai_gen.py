from utils.image_gen import generate_image
from models.mistral import mistral_chat
from models.cerebras import cerebras_chat
import logging
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import aiohttp
from utils.gallery import gallery
import discord

logger = logging.getLogger('AlphaLLM')

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
        with open("preprompt.txt", "r", encoding="utf-8") as file:
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

        bot_id = bot.user.id if isinstance(bot, discord.Client) else bot.id

        match bot_id:
            case 1370685184269352962: # Mistral bot ID
                response = await mistral_chat(user_message, preprompt, tools, bot, user, parameters)
                logger.info("Réponse générée par Mistral")
            #case 1370683258274185349: # Gemini bot ID
                #gemini_chat(user_message, preprompt, tools, bot, user, parameters)
            case _: # AlphaLLM bot ID
                response = await cerebras_chat(user_message, preprompt, tools, bot, user, parameters)
                logger.info("Réponse générée par Cerebras")

        return response

    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse : {e}")
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