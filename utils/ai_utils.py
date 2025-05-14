import logging
import re
from utils.ai_gen import chat
from utils.md_converter import md_conversion
from utils.web_process import get_text_from_url
from utils.memory_ai import add_memory, get_history, initialize
from utils.user_config import get_perso_preprompt

logger = logging.getLogger('AlphaLLM')
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
            link_content = await get_text_from_url(link)
            
            if link_content:
                processed_content += f"\nContenu :\n{link_content[:2000]}"
                logger.debug(f"Contenu récupéré: {link} ({len(link_content)} caractères)")
            else:
                processed_content += f"\nLe lien `{link}` est inaccessible"
                logger.warning(f"Lien inaccessible: {link}")
                
        except Exception as e:
            logger.error(f"Erreur traitement lien {link}: {str(e)}")
            processed_content += f"\n[Erreur de traitement du lien {link}]"
    
    logger.debug(f"Traitement terminé. Taille finale: {len(processed_content)} caractères")
    return processed_content

async def get_conversation_history(user_id: int, server_id: int) -> str:
    """Récupère l'historique contextuel depuis la mémoire vectorielle"""
    try:
        logger.debug(f"Récupération historique pour {user_id}")
        history = await get_history(user_id, server_id)      
        if not history:
            logger.debug(f"Aucun historique trouvé pour {user_id} sur {server_id}")
            return ""
        
        context = "\n".join([f"[{entry['created_at']}] {entry['content']}" for entry in history[:10]])
        logger.debug(f"Historique chargé: {len(history)} entrées")
        return context
        
    except Exception as e:
        logger.error(f"🔴 Erreur historique: {str(e)}", exc_info=True)
        return ""

async def generate_response(user_id: int, server_id: int, raw_content: str, attachments: list, parameters: dict) -> str:
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
            history_context = await get_conversation_history(user_id, server_id)
        else:
            history_context = ""
        
        full_prompt = f"""
        [Conversation history]
        {history_context}
        
        [New message]
        {processed_content}
        """
        logger.debug(f"Prompt final:\n{full_prompt[:500]}...")
        
        response = await chat(full_prompt, perso_preprompt, parameters)
        logger.debug(f"Réponse générée: {response[:500]}...")

        if not isinstance(response, bytes):
            if parameters.get("history", True):
                logger.debug("Mise à jour de la mémoire")
                try:
                    combined_text = f"Utilisateur: {processed_content}\nAssistant: {response}"
                    await add_memory(int(user_id), int(server_id), combined_text)

                    logger.debug("Mémoire mise à jour avec succès")
                except Exception as e:
                    logger.error(f"Erreur mise à jour mémoire: {str(e)}")
        
        return response
        
    except Exception as e:
        logger.critical(f"🔴 Erreur critique: {str(e)}", exc_info=True)
        return "❌ Une erreur inattendue s'est produite. Veuillez réessayer."
