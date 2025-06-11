import logging
from dotenv import load_dotenv
import os
import json
import asyncio
import re
import perplexity_async  # Bibliothèque pour interagir avec Perplexity

logger = logging.getLogger('AlphaLLM')

load_dotenv()

async def extract_clean_answer(response):
    """Extrait et nettoie la réponse de Perplexity"""
    try:
        if response and isinstance(response, dict):
            if 'answer' in response:
                return response['answer'].strip()
            # Gestion des formats différents de réponse
            elif 'text' in response:
                return response['text'].strip()
        return ""
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de la réponse: {e}")
        return ""

def convert_to_plain_text(markdown_text):
    """Convertit le markdown en texte brut pour un affichage simple"""
    # Suppression des titres markdown
    text = re.sub(r'#+\s+', '', markdown_text)
    # Suppression des caractères spéciaux markdown
    text = re.sub(r'[*_~`]', '', text)
    # Simplification des listes
    text = re.sub(r'^\s*[-*]\s+', '- ', text, flags=re.MULTILINE)
    # Suppression des blocs de code
    text = re.sub(r'```[^`]*```', '', text)
    return text.strip()

def is_complete_response(text):
    """Vérifie si la réponse est complète"""
    if not text:
        return False
    # Vérifie si la réponse contient |end_task| ou semble se terminer naturellement
    if "|end_task|" in text:
        return True
    # Vérifier si la réponse semble complète (phrases terminées, longueur minimale)
    if len(text) > 150 and any(text.strip().endswith(c) for c in ['.', '!', '?', ':', ';']):
        return True
    return False

def format_query(query, preprompt, output_format="markdown"):
    """Formate la requête avec le preprompt et ajoute des instructions de format"""
    formatted_query = f"{preprompt}\n\n{query}"
    
    if output_format == "markdown":
        instruction = "\n\nPlease write the answer in Markdown format. Use ## for titles, **bold** for important content, and - or 1. for lists. Write the answer completely. When the answer is finished, be sure to add '|end_task|' at the end."
    else:
        instruction = "\n\nPlease write the answer concisely in plain text format. Do not use special characters or Markdown syntax. When the answer is finished, be sure to add '|end_task|' at the end."
    
    return formatted_query + instruction

async def get_complete_response(client, query, max_retries=3, language='fr-FR'):
    """Tente d'obtenir une réponse complète avec plusieurs essais si nécessaire"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Tentative {attempt + 1}/{max_retries} d'obtenir une réponse")
            response = await client.search(
                query=query,
                mode='auto',  # Mode par défaut
                stream=False,
                language=language,
                sources=["web"],  # Sources: web, scholar, social
                incognito=True  # Mode incognito pour les utilisateurs avec compte
            )
            
            if response:
                clean_answer = await extract_clean_answer(response)
                if clean_answer and is_complete_response(clean_answer):
                    logger.info(f"Réponse complète reçue (longueur: {len(clean_answer)})")
                    return response
                else:
                    logger.warning("Réponse incomplète détectée, nouvel essai...")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(3)
            else:
                logger.warning("La réponse est None, nouvel essai...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Tentative {attempt + 1} échouée: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
            else:
                raise e
    
    logger.warning("Tous les essais ont échoué, retournant None")
    return None

async def perplexity_chat(user_message, preprompt, tools, bot, user, parameters):
    try:
        # Extraire les paramètres pertinents
        output_format = parameters.get("output_format", "markdown")
        language = parameters.get("language", "fr-FR")  # Par défaut en français
        mode = parameters.get("mode", "auto")  # Mode par défaut
        
        # Formatage de la requête avec le preprompt
        formatted_query = format_query(user_message, preprompt, output_format)
        
        # Initialisation du client
        perplexity_cli = await perplexity_async.Client(cookies={})
        
        # Obtenir la réponse complète
        response = await get_complete_response(perplexity_cli, formatted_query, language=language)
        
        if response:
            clean_answer = await extract_clean_answer(response)
            
            # Nettoyer la réponse
            if "|end_task|" in clean_answer:
                clean_answer = clean_answer.replace("|end_task|", "").strip()
                
            # Convertir en texte brut si demandé
            if output_format == "plain":
                return convert_to_plain_text(clean_answer)
            else:
                return clean_answer
        else:
            return "Je n'ai pas pu générer une réponse. Veuillez réessayer."
            
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse Perplexity : {e}")
        return f"Erreur lors de la génération de la réponse : {e}"
    






if __name__ == "__main__":
    asyncio.run(perplexity_chat(input("Entrez votre message : "), "Réponds en français", [], None, None, {"output_format": "markdown", "language": "fr-FR"}))