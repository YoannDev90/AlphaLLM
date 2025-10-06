import logging
from utils.config import (
    LOGGER_NAME, get_base_preprompt, IMAGE_ENHANCER_PREPROMPT,
    CLOUDFLARE_WORKERS_ACCOUNT_ID, CLOUDFLARE_WORKERS_API_KEY, AIML_API_KEY,
    API_ENDPOINTS_OTHER, MAX_TOKENS_IMAGE_DESCRIPTION
)
import re
from utils.ai_gen import chat
from utils.md_converter import md_conversion
from utils.web_process import crawl
from utils.memory_ai import add_memory, get_history, get_hybrid_history, initialize, search_similar_memories
from utils.user_config import get_perso_preprompt
import litellm
from litellm.integrations.opik.opik import OpikLogger
import asyncio
import requests
import json

logger = logging.getLogger(LOGGER_NAME)
URL_REGEX = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+\/?(?:[^\s]*[^\s.,])?'

async def process_attachments(raw_content: str, attachments: list) -> str:
    """Traite les pièces jointes et les liens avec journalisation détaillée"""
    processed_content = raw_content
    docs = []
    links = re.findall(URL_REGEX, raw_content)
    
    logger.debug(f"Début traitement de {len(attachments)} pièces jointes et {len(links)} liens")
    
    for attachment in attachments:
        if attachment.content_type.startswith("image"):
            processed_content += f"\n[Image jointe: {attachment.url}]"
            logger.debug(f"Image détectée: {attachment.url}")
        else:
            docs.append(attachment.url)
            logger.debug(f"Document à convertir: {attachment.url}")
    
    for doc_url in docs:
        try:
            doc_content = await md_conversion(doc_url)
            processed_content += f"\nContenu du document :\n{doc_content}"
            logger.debug(f"Document converti: {doc_url} ({len(doc_content)} caractères)")
        except Exception as e:
            logger.error(f"Échec conversion document: {doc_url} - {str(e)}")
            processed_content += f"\n[Erreur de conversion du document {doc_url}]"
    
    for link in set(links):
        try:
            logger.debug(f"Traitement du lien: {link}")
            processed_content += f"\n\nLien : {link}"
            link_content = await crawl(link)
            
            if link_content:
                processed_content += f"\nContenu :\n{link_content}"
                logger.debug(f"Contenu récupéré: {link} ({len(link_content)} caractères)")
            else:
                processed_content += f"\nLe lien `{link}` est inaccessible"
                logger.warning(f"Lien inaccessible: {link}")
                
        except Exception as e:
            print(e)
            logger.error(f"Erreur traitement lien {link}: {str(e)}")
            processed_content += f"\n[Erreur de traitement du lien {link}]"
    
    logger.debug(f"Traitement terminé. Taille finale: {len(processed_content)} caractères")
    return processed_content

async def get_conversation_history(user_id: int, server_id: int, current_query: str = "") -> str:
    """Récupère l'historique contextuel depuis la mémoire vectorielle"""
    try:
        logger.debug(f"Récupération historique pour {user_id}")
        
        if current_query.strip():
            logger.debug(f"🔍 Recherche hybride pour: '{current_query[:50]}...'")
            history = await get_hybrid_history(user_id, server_id, current_query)
            logger.debug(f"📊 Historique hybride (récent + similaire) chargé: {len(history)} entrées")
        else:
            logger.debug("📅 Utilisation de l'historique chronologique")
            history = await get_history(user_id, server_id)
            logger.debug(f"📊 Historique chronologique chargé: {len(history)} entrées")

        if not history:
            logger.debug(f"Aucun historique trouvé pour {user_id} sur {server_id}")
            return ""
        
        context = "\n".join([f"[{entry['created_at']}] {entry['content']}" for entry in history[:10]])
        return context
        
    except Exception as e:
        logger.error(f"🔴 Erreur historique: {str(e)}", exc_info=True)
        return ""

async def generate_response(user_id: int, server_id: int, raw_content: str, attachments: list, bot, user, parameters: dict) -> str:
    """
    Orchestre la génération de réponse avec gestion d'erreurs renforcée
    """    
    try:
        if not getattr(initialize, '_initialized', False):
            await initialize()
            initialize._initialized = True
        
        processed_content = await process_attachments(raw_content, attachments)
        logger.debug(f"Contenu traité: {processed_content[:500]}...")

        perso_preprompt = get_perso_preprompt(user_id) if get_perso_preprompt(user_id) else ""
        
        if parameters.get("history", True):
            logger.debug("Récupération de l'historique de conversation")
            history_context = await get_conversation_history(user_id, server_id, processed_content)
        else:
            history_context = ""

        preprompt = get_base_preprompt()
        perso_preprompt = False
        if parameters.get("preprompt", True):
            perso_preprompt = get_perso_preprompt(user_id)
        messages = await messages_builder(processed_content, preprompt, perso_preprompt, history_context)

        response = await chat(messages, bot, user, parameters)

        if not isinstance(response, bytes):
            if parameters.get("history", True):
                logger.debug("Mise à jour de la mémoire")
                try:
                    # Ensure response is a dictionary with the expected structure
                    if isinstance(response, dict) and 'response' in response:
                        response_text = response['response']
                        combined_text = {
                            "user": processed_content,
                            "assistant": response_text
                        }
                        await add_memory(int(user_id), int(server_id), combined_text, response_text)
                        logger.debug("Mémoire mise à jour avec succès")
                    else:
                        logger.warning(f"Format de réponse inattendu pour la mise à jour de la mémoire: {type(response)}")
                except Exception as e:
                    logger.error(f"Erreur mise à jour mémoire: {str(e)}")
        
        return response
        
    except Exception as e:
        logger.critical(f"🔴 Erreur critique: {str(e)}", exc_info=True)
        return "❌ Une erreur inattendue s'est produite. Veuillez réessayer."

async def search_memory(user_id: int, server_id: int, query: str, limit: int = 5) -> str:
    """Recherche dans la mémoire et retourne les résultats formatés"""
    try:
        results = await search_similar_memories(user_id, server_id, query, limit)
        if not results:
            return "Aucune mémoire similaire trouvée."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            distance = result.get('distance', 0)
            similarity = 1 - distance
            formatted_results.append(
                f"{i}. [Similarité: {similarity:.2%}] [{result['created_at']}]\n{result['content']}"
            )
        
        return "\n\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Erreur de recherche mémoire: {str(e)}")
        return f"Erreur lors de la recherche: {str(e)}"

async def enhance_image_prompt(original_prompt, number=2):
    try:
        # Créer les tâches selon le nombre demandé
        tasks = []
        models = ["groq/llama-3.1-8b-instant", "cerebras/llama3.1-8b"]
        
        # On génère au maximum 4 prompts améliorés
        for i in range(min(number, 4)):
            model = models[i % len(models)]  # Alterner entre les modèles
            messages=[
                    {"role": "system", "content": IMAGE_ENHANCER_PREPROMPT},
                    {"role": "user", "content": original_prompt}
                ]
            task = litellm.acompletion(
                model=model,
                messages=messages
            )
            tasks.append(task)
        
        # Exécuter toutes les tâches en parallèle
        results = await asyncio.gather(*tasks)
        
        # Construire le dictionnaire de résultats
        result = {}
        for i, response in enumerate(results, 1):
            result[i] = response.choices[0].message.content
        
        return result
        
    except Exception as e:
        logger.error(f"Error enhancing image prompt: {e}")
        return {1: original_prompt}
    
async def messages_builder(user_input, system_prompt, perso_preprompt, history):
    messages = []
    if perso_preprompt:
        system_prompt += f"\n\n{perso_preprompt}"
    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})
    
    # Gérer l'historique correctement
    if history:
        if isinstance(history, str):
            # Si l'historique est une chaîne, l'ajouter comme contexte système
            if history.strip():
                messages.append({"role": "system", "content": f"Contexte de conversation précédente:\n{history}"})
        elif isinstance(history, list):
            # Si l'historique est une liste de messages, l'étendre
            messages.extend(history)
    
    messages.append({"role": "user", "content": user_input})

    return messages

def summarize(input_text, max_length):
    cloudflare_base = API_ENDPOINTS_OTHER.get("cloudflare_ai", "https://api.cloudflare.com/client/v4/accounts")
    url = f"{cloudflare_base}/{CLOUDFLARE_WORKERS_ACCOUNT_ID}/ai/run/@cf/facebook/bart-large-cnn"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_WORKERS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "input_text": input_text,
        "parameters": {
            "max_length": max_length
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    result = response.json()
    result = result['result']['summary']
    return result

def describe_image(image_url):
    url = API_ENDPOINTS_OTHER.get("aiml", "https://api.aimlapi.com/chat/completions")
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {AIML_API_KEY}'
    }
    payload = json.dumps({
        "model": "meta-llama/Llama-Vision-Free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ],
        "max_tokens": MAX_TOKENS_IMAGE_DESCRIPTION
    })

    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    result = response.json()
    return result