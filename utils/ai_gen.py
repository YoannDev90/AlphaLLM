from utils.image_gen import generate_image
from models.mistral import mistral_chat
from models.deepseek import deepseek_chat
from models.phi import phi_chat
from models.qwen import qwen_chat
from models.openai import openai_chat
from models.evilgpt import evilgpt_chat
from models.llama import llama_chat
from models.gemini import gemini_chat
from models.perplexity import perplexity_chat
from models.grok import grok_chat
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
                    "description": "Image size to generate in pixels (width x height), max 2048x2048, min 512x512",
                    "examples": ["512x512", "1024x1024", "2048x2048", "2048x1024", "1024x2048"],
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
            case 1370682029460684850: # DeepSeek bot ID
                response = await deepseek_chat(user_message, preprompt, tools, bot, user, parameters)
                logger.info("Réponse générée par DeepSeek")
            case 1370683258274185349: # Gemini bot ID
                response = await gemini_chat(user_message, preprompt, tools, bot, user, parameters)
                logger.info("Réponse générée par Gemini")
            case 1370685419557224538: # Phi bot ID
                response = await phi_chat(user_message, preprompt, tools, bot, user, parameters)
                logger.info("Réponse générée par Phi")
            case 1370686144542539846: # Qwen bot ID
                response = await qwen_chat(user_message, preprompt, tools, bot, user, parameters)
                logger.info("Réponse générée par Qwen")
            case 1370683080892747796: # OpenAI bot ID
                response = await openai_chat(user_message, preprompt, tools, bot, user, parameters)
                logger.info("Réponse générée par OpenAI")
            case 1370685660326920252: # EvilGPT bot ID
                response = await evilgpt_chat(user_message, preprompt, tools, bot, user, parameters)
                logger.info("Réponse générée par EvilGPT")
            case 1370683169522847827: # Grok bot ID
                response = await grok_chat(user_message, preprompt, tools, bot, user, parameters)
                logger.info("Réponse générée par Grok")
            case 1370685321703854110: # Llama bot ID
                response = await llama_chat(user_message, preprompt, tools, bot, user, parameters)
                logger.info("Réponse générée par Llama")
            # case 1370681547740418079: #Perplexity bot ID
            #     response = await perplexity_chat(user_message, preprompt)
            #     logger.info("Réponse générée par Perplexity")
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
            try:
                image_data, nsfw = await generate_image(
                    prompt=prompt,
                    width=width,
                    height=height
                )
            except Exception as e:
                logger.error(f"Erreur lors de la génération de l'image : {e}")
                return "❌ Image generation failed."
        if not nsfw:
            await gallery(bot, image_data, prompt, user)
        return image_data
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'image : {e}")
        return f"❌ Erreur lors de l'envoi de l'image : {e}"