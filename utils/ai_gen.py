# from utils.image_gen import generate_image
from models.mistral import mistral_chat
from models.deepseek import deepseek_chat
from models.qwen import qwen_chat
from models.openai import openai_chat
from models.evilgpt import evilgpt_chat
from models.llama import llama_chat
from models.gemini import gemini_chat
from models.perplexity import perplexity_chat
from models.grok import grok_chat
import logging
from utils.config import LOGGER_NAME
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import aiohttp
import discord
import tomllib

logger = logging.getLogger(LOGGER_NAME)

def load_preprompt() -> str:
    """Charge le pré-prompt depuis un fichier"""
    try:
        with open("config.toml", "rb") as file:
            config = tomllib.load(file)
        preprompt = config.get("preprompt", "")
        logger.debug("Preprompt loaded successfully from config.toml")
        now = datetime.now()
        preprompt += f"\nDate: {now.strftime('%Y-%m-%d')}\nHour: CEST {now.strftime('%H:%M:%S')}\n"
        return preprompt
    except Exception as e:
        logger.error(f"Error loading preprompt from config.toml: {str(e)}")
        raise

async def chat(messages, bot, user, parameters):
    try:
        bot_id = bot.user.id if isinstance(bot, discord.Client) else bot.id

        match bot_id:
            case 1370685184269352962: # Mistral bot ID
                logger.debug("Using Mistral model for chat")
                response = await mistral_chat(messages, parameters)
                logger.info("Réponse générée par Mistral")
            case 1370682029460684850: # DeepSeek bot ID
                logger.debug("Using DeepSeek model for chat")
                response = await deepseek_chat(messages, parameters)
                logger.info("Réponse générée par DeepSeek")
            case 1370683258274185349: # Gemini bot ID
                logger.debug("Using Gemini model for chat")
                response = await gemini_chat(messages, parameters)
                logger.info("Réponse générée par Gemini")
            case 1370686144542539846: # Qwen bot ID
                logger.debug("Using Qwen model for chat")
                response = await qwen_chat(messages, parameters)
                logger.info("Réponse générée par Qwen")
            case 1370683080892747796: # OpenAI bot ID
                logger.debug("Using OpenAI model for chat")
                response = await openai_chat(messages, parameters)
                logger.info("Réponse générée par OpenAI")
            case 1370685660326920252: # EvilGPT bot ID
                logger.debug("Using EvilGPT model for chat")
                response = await evilgpt_chat(messages, parameters)
                logger.info("Réponse générée par EvilGPT")
            case 1370683169522847827: # Grok bot ID
                logger.debug("Using Grok model for chat")
                response = await grok_chat(messages, parameters)
                logger.info("Réponse générée par Grok")
            case 1370685321703854110: # Llama bot ID
                logger.debug("Using Llama model for chat")
                response = await llama_chat(messages, parameters)
                logger.info("Réponse générée par Llama")
            case 1370681547740418079: #Perplexity bot ID
                logger.debug("Using Perplexity model for chat")
                response = await perplexity_chat(messages, parameters)
                logger.info("Réponse générée par Perplexity")
            case _: # AlphaLLM bot ID
                response = await llama_chat(messages, parameters)
                logger.info("Réponse générée par Llama")

        return response

    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse : {e}")
        return {
            "response": f"Erreur lors de la génération de la réponse : {e}",
            "usage": 0,
            "model": "error",
            "elapsed_time": "0 seconds"
        }
    
def get_text_model_info(model_name):
    """
    Récupère les informations d'un modèle depuis text_models.toml
    """
    try:
        with open("text_models.toml", "rb") as f:
            models_config = tomllib.load(f)
        
        for key, model in models_config.items():
            if isinstance(model, dict) and model.get("model") == model_name:
                api_key_env = model["api_key"]
                api_key = os.getenv(api_key_env)
                
                if not api_key:
                    raise ValueError(f"Clé d'API {api_key_env} non trouvée dans les variables d'environnement")
                
                result = {
                    "model": model["model"],
                    "api_key": api_key
                }
                
                if "base_url" in model:
                    result["base_url"] = model["base_url"]
                
                return result

        raise ValueError(f"Modèle '{model_name}' non trouvé dans text_models.toml")

    except FileNotFoundError:
        raise ValueError("Fichier text_models.toml non trouvé")
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture de text_models.toml: {str(e)}")

def get_image_model_info(model_name):
    """
    Récupère les informations d'un modèle depuis image_models.toml
    """
    try:
        with open("image_models.toml", "rb") as f:
            models_config = tomllib.load(f)

        for key, model in models_config.items():
            if isinstance(model, dict) and model.get("model") == model_name:
                api_key_env = model["api_key"]
                api_key = os.getenv(api_key_env)

                if not api_key:
                    raise ValueError(f"Clé d'API {api_key_env} non trouvée dans les variables d'environnement")

                result = {
                    "model": model["model"],
                    "api_key": api_key
                }

                if "base_url" in model:
                    result["base_url"] = model["base_url"]

                return result

        raise ValueError(f"Modèle '{model_name}' non trouvé dans image_models.toml")

    except FileNotFoundError:
        raise ValueError("Fichier image_models.toml non trouvé")
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture de image_models.toml: {str(e)}")
