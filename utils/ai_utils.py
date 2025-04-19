# ai_utils.py
import importlib
import logging
import re
from typing import List, Dict
from utils.md_converter import md_conversion
from utils.web_process import get_text_from_url
from utils.memory_ai import add_memory, get_history, initialize

logger = logging.getLogger('AlphaLLM')
URL_REGEX = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+\/?(?:[^\s]*[^\s.,])?'

def load_preprompt() -> str:
    """Charge le pré-prompt depuis un fichier"""
    try:
        with open("config/preprompt.txt", "r", encoding="utf-8") as file:
            preprompt = file.read()
        logger.info("Pré-prompt chargé avec succès")
        return preprompt
    except Exception as e:
        logger.error(f"Erreur lors du chargement du pré-prompt: {str(e)}")
        raise

async def process_attachments(raw_content: str, attachments: list) -> str:
    """Traite les pièces jointes et les liens avec journalisation détaillée"""
    processed_content = raw_content
    docs = []
    links = re.findall(URL_REGEX, raw_content)
    
    logger.debug(f"Début traitement de {len(attachments)} pièces jointes et {len(links)} liens")
    
    # Traitement des fichiers joints
    for attachment in attachments:
        if attachment.content_type.startswith("image"):
            processed_content += f"\n[Image jointe: {attachment.url}]"
            logger.debug(f"Image détectée: {attachment.url}")
        else:
            docs.append(attachment.url)
            logger.info(f"Document à convertir: {attachment.url}")
    
    # Conversion des documents
    for doc_url in docs:
        try:
            doc_content = await md_conversion(doc_url)
            processed_content += f"\nContenu du document :\n{doc_content}"
            logger.success(f"Document converti: {doc_url} ({len(doc_content)} caractères)")
        except Exception as e:
            logger.error(f"Échec conversion document: {doc_url} - {str(e)}")
            processed_content += f"\n[Erreur de conversion du document {doc_url}]"
    
    # Traitement des liens
    for link in set(links):  # Éviter les doublons
        try:
            logger.debug(f"Traitement du lien: {link}")
            processed_content += f"\n\nLien : {link}"
            link_content = await get_text_from_url(link)
            
            if link_content:
                processed_content += f"\nContenu :\n{link_content[:2000]}"  # Limite de taille
                logger.info(f"Contenu récupéré: {link} ({len(link_content)} caractères)")
            else:
                processed_content += f"\nLe lien `{link}` est inaccessible"
                logger.warning(f"Lien inaccessible: {link}")
                
        except Exception as e:
            logger.error(f"Erreur traitement lien {link}: {str(e)}")
            processed_content += f"\n[Erreur de traitement du lien {link}]"
    
    logger.debug(f"Traitement terminé. Taille finale: {len(processed_content)} caractères")
    return processed_content

async def get_conversation_history(user_id: int) -> str:
    """Récupère l'historique contextuel depuis la mémoire vectorielle"""
    try:
        logger.debug(f"Récupération historique pour {user_id}")
        history = await get_history(str(user_id))
        
        if not history:
            logger.info(f"Aucun historique trouvé pour {user_id}")
            return ""
        
        # Formatage: 5 dernières entrées maximum
        context = "\n".join([f"[{entry['created_at']}] {entry['content']}" 
                           for entry in history[:5]])
        logger.info(f"Historique chargé: {len(history)} entrées")
        return context
        
    except Exception as e:
        logger.error(f"🔴 Erreur historique: {str(e)}", exc_info=True)
        return ""

async def generate_response(user_id: int, raw_content: str, attachments: list, model_name: str) -> str:
    """
    Orchestre la génération de réponse avec gestion d'erreurs renforcée
    """
    logger.info(f"Début génération réponse pour {user_id} avec {model_name}")
    
    try:
        # Initialisation globale si nécessaire
        if not getattr(initialize, '_initialized', False):
            await initialize()
            initialize._initialized = True
        
        # Traitement du contenu
        processed_content = await process_attachments(raw_content, attachments)
        logger.debug(f"Contenu traité: {processed_content[:100]}...")
        
        # Récupération contexte
        history_context = await get_conversation_history(user_id)
        
        # Construction du prompt
        full_prompt = f"""
        [Historique de conversation]
        {history_context}
        
        [Nouveau message]
        {processed_content}
        
        [Instructions]
        Réponds de manière concise et pertinente en français.
        """
        logger.debug(f"Prompt final:\n{full_prompt[:500]}...")
        
        # Chargement dynamique du modèle
        try:
            module_name = model_name.replace("-", "_")
            model_module = importlib.import_module(f"models.{module_name}")
            generate_fn = getattr(model_module, module_name, None)
            
            if not generate_fn:
                raise AttributeError(f"Fonction {module_name} manquante dans {module_name}")
                
        except Exception as e:
            logger.critical(f"🔴 Erreur chargement modèle: {str(e)}")
            return "⚠️ Erreur technique: modèle indisponible"
        
        # Génération de la réponse
        response = await generate_fn(full_prompt)
        logger.info(f"Réponse générée: {response[:100]}...")
        
        # Mise à jour mémoire (async fire-and-forget)
        try:
            combined_text = f"Utilisateur: {processed_content}\nAssistant: {response}"
            await add_memory(str(user_id), combined_text)
            logger.debug("Mémoire mise à jour avec succès")
        except Exception as e:
            logger.error(f"Erreur mise à jour mémoire: {str(e)}")
        
        return response
        
    except Exception as e:
        logger.critical(f"🔴 Erreur critique: {str(e)}", exc_info=True)
        return "❌ Une erreur inattendue s'est produite. Veuillez réessayer."
