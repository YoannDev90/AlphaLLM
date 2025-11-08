from fastapi import APIRouter, Depends, HTTPException, status
from utils.processing.ai_handler import messages_builder, get_conversation_history
from utils.memory import initialize, get_memory_manager
from utils.config.app_config import API_MODELS_PREPROMPT
from typing import Optional
import asyncio
import json
from . import logger, REQUEST_TIMEOUT
from api.utils.security_utils import get_api_key

router = APIRouter()

@router.get("/generate/text", tags=["generation"])
async def generate_text(
    prompt: str,
    model: Optional[str] = "auto", 
    user_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
    incognito: Optional[bool] = False,
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
        from utils.ai.selector import llm_selector

        history = {"stm": [], "ltm": ""}
        await initialize()
        if not incognito and user_id and conversation_id:
            history = await get_conversation_history(user_id, conversation_id, prompt)
            if history is None:
                history = {"stm": [], "ltm": ""}

        messages = await messages_builder(
            user_input=prompt, 
            system_prompt=API_MODELS_PREPROMPT,
            perso_preprompt="",
            history=history
            )
        
        logger.info(f"Requête API reçue - Modèle: {model}")

        parameters = {
            "history": True, 
            "preprompt": False, 
            "tools": False, 
            "internet": False, 
            "raw": False
        }

        print(history)
        print("-------------------------------------")
        print(messages)
        
        async def generate_response():            
            response = None
            
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
                case "auto" | _:
                    if model.lower() == "auto":
                        selected_model = await llm_selector(prompt)
                        logger.info(f"Modèle sélectionné automatiquement : {selected_model}")
                    else:
                        selected_model = "cerebras/llama3.3-70b"
                        logger.warning(f"Modèle inconnu '{model}', utilisation du modèle par défaut: {selected_model}")
                    
                    match selected_model:
                        case "cerebras/llama3.3-70b":
                            response = await llama_chat(messages, parameters)
                            logger.info("Réponse générée par Llama (auto/défaut)")
                        case "openai/gpt-5":
                            response = await openai_chat(messages, parameters)
                            logger.info("Réponse générée par OpenAI (auto/défaut)")
                        case "mistral/mistral-medium-latest":
                            response = await mistral_chat(messages, parameters)
                            logger.info("Réponse générée par Mistral (auto/défaut)")
                        case "openai/deepseek-v3.1":
                            response = await deepseek_chat(messages, parameters)
                            logger.info("Réponse générée par DeepSeek (auto/défaut)")
                        case "cerebras/qwen-3-32b":
                            response = await qwen_chat(messages, parameters)
                            logger.info("Réponse générée par Qwen (auto/défaut)")
                        case "openai/gemini-2.5-flash":
                            response = await gemini_chat(messages, parameters)
                            logger.info("Réponse générée par Gemini (auto/défaut)")
                        case "openai/sonar":
                            response = await perplexity_chat(messages, parameters)
                            logger.info("Réponse générée par Perplexity (auto/défaut)")
                        case "openai/evil":
                            response = await evilgpt_chat(messages, parameters)
                            logger.info("Réponse générée par EvilGPT (auto/défaut)")
                        case "openai/grok-4":
                            response = await grok_chat(messages, parameters)
                            logger.info("Réponse générée par Grok (auto/défaut)")
                        case "openai/claude-3-5-haiku-20241022":
                            response = await claude_chat(messages, parameters)
                            logger.info("Réponse générée par Claude (auto/défaut)")
                        case "openai/kimi-k2-instruct":
                            response = await kimi_chat(messages, parameters)
                            logger.info("Réponse générée par Kimi (auto/défaut)")
                        case "openai/glm-4.5":
                            response = await glm_chat(messages, parameters)
                            logger.info("Réponse générée par GLM (auto/défaut)")
                        case "openai/phi-4":
                            response = await phi_chat(messages, parameters)
                            logger.info("Réponse générée par Phi (auto/défaut)")
                        case "cohere/command-r":
                            response = await cohere_chat(messages, parameters)
                            logger.info("Réponse générée par Cohere (auto/défaut)")
                        case _:
                            logger.warning(f"Modèle sélectionné inconnu '{selected_model}', utilisation de Llama par défaut")
                            response = await llama_chat(messages, parameters)
                            logger.info("Réponse générée par Llama (fallback)")

            if response is None:
                logger.error("Aucune réponse n'a été générée")
                raise ValueError("Aucune réponse générée par le modèle")
            
            logger.debug(f"Réponse brute: {str(response)}")

            if not incognito and user_id and conversation_id:
                response_text = response.get('response', '')
                combined_text = {
                    "user": prompt,
                    "assistant": response_text
                }
                manager = get_memory_manager()
                await manager.add_conversation_message(
                    user_id, 
                    conversation_id, 
                    json.dumps(combined_text, ensure_ascii=False),
                    role="conversation"
                )
                logger.debug("Mémoires utilisateur et assistant ajoutées à la base de données")
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
        return {"status": "error", "message": "Une erreur interne s'est produite lors de la génération du texte."}