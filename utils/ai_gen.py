# from utils.image_gen import generate_image
from utils.llm_selector import llm_selector
import logging
from utils.config import LOGGER_NAME, BOTS_IDS
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import aiohttp
import discord
import tomllib

from models.text.mistral import mistral_chat
from models.text.deepseek import deepseek_chat
from models.text.gemini import gemini_chat
from models.text.qwen import qwen_chat
from models.text.openai import openai_chat
from models.text.evilgpt import evilgpt_chat
from models.text.grok import grok_chat
from models.text.llama import llama_chat
from models.text.perplexity import perplexity_chat
from models.text.claude import claude_chat
from models.text.cohere import cohere_chat
from models.text.glm import glm_chat
from models.text.kimi import kimi_chat
from models.text.phi import phi_chat

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

async def chat(messages: list, bot: discord.Client, user: discord.User, parameters: dict)-> dict:
    try:
        model = parameters.get("model", bot.user.id if isinstance(bot, discord.Client) else bot.id)

        match model:
            case id if id == BOTS_IDS.get("mistral") or id == "mistral":
                logger.debug("Using Mistral model for chat")
                response = await mistral_chat(messages, parameters)
                logger.info("Réponse générée par Mistral")
            case id if id == BOTS_IDS.get("deepseek") or id == "deepseek":
                logger.debug("Using DeepSeek model for chat")
                response = await deepseek_chat(messages, parameters)
                logger.info("Réponse générée par DeepSeek")
            case id if id == BOTS_IDS.get("gemini") or id == "gemini":
                logger.debug("Using Gemini model for chat")
                response = await gemini_chat(messages, parameters)
                logger.info("Réponse générée par Gemini")
            case id if id == BOTS_IDS.get("qwen") or id == "qwen":
                logger.debug("Using Qwen model for chat")
                response = await qwen_chat(messages, parameters)
                logger.info("Réponse générée par Qwen")
            case id if id == BOTS_IDS.get("chatgpt") or id == "openai":
                logger.debug("Using OpenAI model for chat")
                response = await openai_chat(messages, parameters)
                logger.info("Réponse générée par OpenAI")
            case id if id == BOTS_IDS.get("evilgpt") or id == "evilgpt":
                logger.debug("Using EvilGPT model for chat")
                response = await evilgpt_chat(messages, parameters)
                logger.info("Réponse générée par EvilGPT")
            case id if id == BOTS_IDS.get("grok") or id == "grok":
                logger.debug("Using Grok model for chat")
                response = await grok_chat(messages, parameters)
                logger.info("Réponse générée par Grok")
            case id if id == BOTS_IDS.get("llama") or id == "llama":
                logger.debug("Using Llama model for chat")
                response = await llama_chat(messages, parameters)
                logger.info("Réponse générée par Llama")
            case id if id == BOTS_IDS.get("perplexity") or id == "perplexity":
                logger.debug("Using Perplexity model for chat")
                response = await perplexity_chat(messages, parameters)
                logger.info("Réponse générée par Perplexity")
            case id if id == BOTS_IDS.get("claude") or id == "claude":
                response = await claude_chat(messages, parameters)
                logger.info("Réponse générée par Claude")
            case id if id == BOTS_IDS.get("cohere") or id == "command":
                response = await cohere_chat(messages, parameters)
                logger.info("Réponse générée par Command")
            case id if id == BOTS_IDS.get("glm") or id == "glm":
                response = await glm_chat(messages, parameters)
                logger.info("Réponse générée par GLM")
            case id if id == BOTS_IDS.get("kimi") or id == "kimi":
                response = await kimi_chat(messages, parameters)
                logger.info("Réponse générée par Kimi")
            case id if id == BOTS_IDS.get("phi") or id == "phi":
                response = await phi_chat(messages, parameters)
                logger.info("Réponse générée par Phi")
            case _: # AlphaLLM bot ID
                logger.debug("Using LLM Selector to choose the best model")
                selected_model = await llm_selector(messages[-1]['content'])
                logger.info(f"Model selected by LLM Selector: {selected_model}")
                match selected_model:
                    case "cerebras/llama3.3-70b":
                        response = await llama_chat(messages, parameters)
                        logger.info("Réponse générée par Llama")
                    case "openai/gpt-5":
                        response = await openai_chat(messages, parameters)
                        logger.info("Réponse générée par OpenAI")
                    case "mistral/mistral-medium-latest":
                        response = await mistral_chat(messages, parameters)
                        logger.info("Réponse générée par Mistral")
                    case "cerebras/qwen-3-32b":
                        response = await qwen_chat(messages, parameters)
                        logger.info("Réponse générée par Qwen")
                    case "openai/gemini-2.5-flash":
                        response = await gemini_chat(messages, parameters)
                        logger.info("Réponse générée par Gemini")
                    case "openai/sonar":
                        response = await perplexity_chat(messages, parameters)
                        logger.info("Réponse générée par Perplexity")
                    case "openai/evil":
                        response = await evilgpt_chat(messages, parameters)
                        logger.info("Réponse générée par EvilGPT")
                    case "openai/grok-4":
                        response = await grok_chat(messages, parameters)
                        logger.info("Réponse générée par Grok")
                    case "openai/claude-3-5-haiku-20241022":
                        response = await claude_chat(messages, parameters)
                        logger.info("Réponse générée par Claude")
                    case "openai/kimi-k2-instruct":
                        response = await kimi_chat(messages, parameters)
                        logger.info("Réponse générée par Kimi")
                    case "openai/deepseek-v3.1":
                        response = await deepseek_chat(messages, parameters)
                        logger.info("Réponse générée par DeepSeek")
                    case "openai/glm-4.5":
                        response = await glm_chat(messages, parameters)
                        logger.info("Réponse générée par GLM")
                    case "openai/phi-4":
                        response = await phi_chat(messages, parameters)
                        logger.info("Réponse générée par Phi")
                    case "cohere/command-r":
                        response = await cohere_chat(messages, parameters)
                        logger.info("Réponse générée par Cohere")

        return response

    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse : {e}")
        return {
            "response": f"Erreur lors de la génération de la réponse : {e}",
            "usage": 0,
            "model": "error",
            "elapsed_time": "0 seconds"
        }