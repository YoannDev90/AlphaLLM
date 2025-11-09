from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from api.utils.security_utils import get_api_key
from utils.processing.ai_handler.enhancement import summarize
import requests
import logging
import asyncio
import time
import json
import re
from utils.config import (
    API_ENDPOINTS_TEXT, MODELS_CONFIG_TEXT, LOGGER_NAME,
    CF_WORKERS_ACC_ID, CF_WORKERS_API_KEY
)
from . import REQUEST_TIMEOUT

logger = logging.getLogger(LOGGER_NAME)
router = APIRouter()

@router.get("/summarize", 
            tags=["text"],
            summary="Résumer un texte",
            description="Génère un résumé automatique d'un texte long en utilisant l'IA Cloudflare",
            response_description="Résumé du texte avec métadonnées")
async def summarize_text(
    long_text: str = Query(..., description="Texte à résumer", min_length=1, max_length=50000),
    max_length: int = Query(256, description="Longueur maximale du résumé (entre 10 et 1000 caractères)", ge=10, le=1000),
    api_key: Optional[str] = Depends(get_api_key)
):
    start_time = time.time()
    
    try:
        if not CF_WORKERS_ACC_ID or not CF_WORKERS_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service de résumé temporairement indisponible"
            )
        
        if not long_text or len(long_text.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le texte à résumer ne peut pas être vide"
            )
        
        if max_length < 10 or max_length > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La longueur maximale doit être entre 10 et 1000 caractères"
            )
        
        text_length = len(long_text)
        
        async def generate_summary():
            return summarize(long_text, max_length)
        
        summary = await asyncio.wait_for(
            generate_summary(),
            timeout=REQUEST_TIMEOUT
        )
        
        elapsed_time = time.time() - start_time
        summary_length = len(summary) if summary else 0
        
        return {
            "status": "success",
            "summary": summary,
            "metadata": {
                "original_length": text_length,
                "summary_length": summary_length,
                "max_length": max_length,
                "processing_time": round(elapsed_time, 2),
                "compression_ratio": round((text_length - summary_length) / text_length * 100, 2) if text_length > 0 else 0
            }
        }
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Timeout lors de la génération du résumé"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de la génération du résumé"
        )

@router.get("/conv_name", 
           tags=["text"],
           summary="Générer un titre de conversation",
           description="Génère un titre descriptif pour une conversation basé sur les messages échangés",
           response_description="Titre de conversation avec métadonnées")
async def generate_conversation_name(
    messages: str = Query(..., description="Messages de la conversation au format JSON (liste d'objets avec 'role' et 'content')", min_length=10),
    api_key: Optional[str] = Depends(get_api_key)
):
    start_time = time.time()
    
    try:
        # Parser le JSON des messages
        try:
            messages_data = json.loads(messages)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format JSON invalide pour les messages"
            )
        
        if not messages_data or len(messages_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La liste des messages ne peut pas être vide"
            )
        
        valid_messages = []
        for i, msg in enumerate(messages_data):
            if not isinstance(msg, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Le message {i} doit être un objet JSON"
                )
            
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if content and content.strip():
                valid_messages.append({"role": role, "content": content.strip()})
        
        if not valid_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun message avec du contenu valide trouvé"
            )
        
        messages_text = ""
        total_chars = 0
        for msg in valid_messages:
            role = msg["role"]
            content = msg["content"]
            line = f"{role}: {content}\n"
            messages_text += line
            total_chars += len(content)
        
        max_chars = 8000
        if len(messages_text) > max_chars:
            messages_text = messages_text[:max_chars] + "..."
        
        async def generate_title():
            return await conversation_title(messages_text.strip())
        
        title = await asyncio.wait_for(
            generate_title(),
            timeout=REQUEST_TIMEOUT
        )
        
        elapsed_time = time.time() - start_time
        
        return {
            "status": "success",
            "conversation_title": title,
            "metadata": {
                "messages_count": len(messages_data),
                "valid_messages_count": len(valid_messages),
                "total_characters": total_chars,
                "processing_time": round(elapsed_time, 2)
            }
        }
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Timeout lors de la génération du titre de conversation"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de la génération du titre de conversation"
        )

async def conversation_title(input_text: str) -> str:
    try:
        messages = [
            {
                "role": "user", 
                "content": f"Create a short title (3-5 words) for this conversation:\n\n{input_text}"
            }
        ]
        
        api_url = API_ENDPOINTS_TEXT.get("hackclub", "https://ai.hackclub.com/chat/completions")
        model_name = MODELS_CONFIG_TEXT.get("llm_selector", "openai/gpt-oss-20b")
        
        response = requests.post(
            api_url,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "AlphaLLM-API/1.0"
            },
            json={
                "model": model_name,
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.4
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                raise Exception("Réponse API invalide")
            
            title = data["choices"][0]["message"]["content"].strip()
            
            if not title:
                title = "Conversation sans titre"
            
            title = title.strip('"\'.,!?;:')
            
            if len(title) > 80:
                title = title[:77] + "..."
            
            return title
                
        elif response.status_code == 429:
            raise Exception("Trop de requêtes, veuillez réessayer plus tard")
        elif response.status_code >= 500:
            raise Exception("Service temporairement indisponible")
        else:
            raise Exception(f"Erreur API: {response.status_code}")
    
    except requests.exceptions.Timeout:
        raise Exception("Timeout lors de la génération du titre")
    except requests.exceptions.ConnectionError:
        raise Exception("Impossible de se connecter au service de génération")
    except requests.exceptions.RequestException:
        raise Exception("Erreur lors de la communication avec l'API")
    except Exception as e:
        raise