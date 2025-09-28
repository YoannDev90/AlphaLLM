from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import asyncio

from . import logger, REQUEST_TIMEOUT
from api.utils.security_utils import get_api_key

router = APIRouter()

@router.get("/generate/text", tags=["generation"])
async def generate_text(
    model: str, 
    prompt: str,
    api_key: Optional[str] = Depends(get_api_key)
):
    try:
        from models.text.mistral import mistral_chat
        from models.text.deepseek import deepseek_chat
        from models.text.qwen import qwen_chat
        from models.text.openai import openai_chat
        from models.text.evilgpt import evilgpt_chat
        from models.text.llama import llama_chat
        from models.text.gemini import gemini_chat
        from models.text.perplexity import perplexity_chat
        from models.text.grok import grok_chat
        from models.text.claude import claude_chat
        from models.text.cohere import cohere_chat
        from models.text.glm import glm_chat
        from models.text.kimi import kimi_chat
        from models.text.phi import phi_chat
                
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        parameters = {
            "history": False, 
            "preprompt": False, 
            "tools": False, 
            "internet": False, 
            "raw": False
        }
        
        async def generate_response():
            match model.lower():
                case "mistral":
                    response = await mistral_chat(messages, parameters)
                    logger.info("Réponse générée par Mistral")
                case "deepseek":
                    response = await deepseek_chat(messages, parameters)
                    logger.info("Réponse générée par DeepSeek")
                case "qwen":
                    response = await qwen_chat(messages, parameters)
                    logger.info("Réponse générée par Qwen")
                case "openai":
                    response = await openai_chat(messages, parameters)
                    logger.info("Réponse générée par OpenAI")
                case "evilgpt":
                    response = await evilgpt_chat(messages, parameters)
                    logger.info("Réponse générée par EvilGPT")
                case "llama":
                    response = await llama_chat(messages, parameters)
                    logger.info("Réponse générée par Llama")
                case "gemini":
                    response = await gemini_chat(messages, parameters)
                    logger.info("Réponse générée par Gemini")
                case "perplexity":
                    response = await perplexity_chat(messages, parameters)
                    logger.info("Réponse générée par Perplexity")
                case "grok":
                    response = await grok_chat(messages, parameters)
                    logger.info("Réponse générée par Grok")
                case "claude":
                    response = await claude_chat(messages, parameters)
                    logger.info("Réponse générée par Claude")
                case "cohere":
                    response = await cohere_chat(messages, parameters)
                    logger.info("Réponse générée par Cohere")
                case "glm":
                    response = await glm_chat(messages, parameters)
                    logger.info("Réponse générée par GLM")
                case "kimi":
                    response = await kimi_chat(messages, parameters)
                    logger.info("Réponse générée par Kimi")
                case "phi":
                    response = await phi_chat(messages, parameters)
                    logger.info("Réponse générée par Phi")
                case _:
                    response = await llama_chat(messages, parameters)
                    logger.info("Réponse générée par Llama (modèle par défaut)")
            return response
        
        response = await asyncio.wait_for(
            generate_response(),
            timeout=REQUEST_TIMEOUT
        )
        
        return {"status": "success", "response": response}
    except asyncio.TimeoutError:
        logger.error(f"Timeout lors de la génération de texte avec le modèle {model}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Timeout lors de la génération de texte"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la génération du texte : {str(e)}")
        return {"status": "error", "message": str(e)}