import datetime
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, Union, Dict
from utils.memory import initialize_memory_manager, get_memory_manager
from utils.ai_process.llm_selector import LLMSelector
import logging
from utils.ai_process.ai_utils import summarize
from utils.handlers.files import FileHandler
from config import LOGGER_NAME, AVAILABLE_MODELS, read_file

logger = logging.getLogger(LOGGER_NAME)

@dataclass
class RequestParameters:
    history: bool = True
    preprompt: bool = True
    tools: bool = False
    internet: bool = False
    audio: bool = False
    raw: bool = False
    model: Optional[str] = None

class Origin:
    """Classe pour définir l'origine de la requête avec des attributs supplémentaires pour DISCORD."""
    
    def __init__(self, name, message=None, bot=None):
        self.name = name
        self.message = message
        self.bot = bot
    
    def __str__(self):
        return self.name
    
    def __eq__(self, other):
        if isinstance(other, Origin):
            return self.name == other.name
        return False
    
    def __hash__(self):
        return hash(self.name)

Origin.API = Origin("api")
Origin.DISCORD = Origin("discord")

class Model(Enum):
    """Enum pour définir les modèles disponibles."""
    AUTO = "auto"
    CLAUDE = "claude"
    COHERE = "cohere"
    DEEPSEEK = "deepseek"
    EVILGPT = "evilgpt"
    GEMINI = "gemini"
    GLM = "glm"
    GRANITE = "granite"
    GROK = "grok"
    HERMES = "hermes"
    HUNYUAN = "hunyuan"
    JAMBA = "jamba"
    KIMI = "kimi"
    LLAMA = "llama"
    LONGCAT = "longcat"
    MERCURY = "mercury"
    MINIMAX = "minimax"
    MISTRAL = "mistral"
    NEMOTRON = "nemotron"
    OPENAI = "openai"
    PHI = "phi"
    QWEN = "qwen"
    ROCINANTE = "rocinante"
    SEED = "seed"
    SONAR = "sonar"
    YI = "yi"

async def unified_manager(
        user_id: int, 
        conv_id: str, 
        input: str, 
        model: Union[str, Model], 
        files: Optional[List[Any]] = None, 
        origin: Optional[Origin] = None, 
        message: Optional[Any] = None, 
        bot: Optional[Any] = None, 
        permission_checker: Optional[Any] = None, 
        stream: bool = False, 
        use_memory: bool = True
    ):
    """
    Fonction pour gérer les requêtes vers les modèles, avec permissions, mémoire, pré/post-traitement et erreurs.

    Args:
        user_id: ID de l'utilisateur.
        conv_id: ID de la conversation.
        input: Texte d'entrée de l'utilisateur.
        model: Modèle à utiliser (e.g., 'claude' or Model.CLAUDE).
        files: Liste des fichiers attachés (optionnel).
        origin: Origine de la requête (API ou Discord, via Origin).
        message: Message supplémentaire pour Discord (optionnel).
        bot: Bot supplémentaire pour Discord (optionnel).
        permission_checker: Vérificateur de permissions pour Discord (optionnel).
        stream: Si True, streaming de la réponse.
        use_memory: Si True, utilise la mémoire. (API seulement)
    """
    origin = origin or Origin.API
    model = model or Model.AUTO.value
    if isinstance(model, Model):
        model = model.value

    if origin == Origin.DISCORD and permission_checker and message:
        authorized, reason = permission_checker.is_authorized(message)
        if not authorized:
            user = message.author if hasattr(message, 'author') else message.user
            logger.debug(f"Message non autorisé de {user.display_name} (ID: {user.id}): {reason}")
            return

    user = message.author if hasattr(message, 'author') else message.user if message else None

    file_handler = None
    processed_files = []
    if files:
        logger.info(f"Files uploaded: {len(files)} file(s) - {[str(f) for f in files]}")
        file_handler = FileHandler(files)
        await file_handler.process_files()
        for file_list in file_handler.saved_files.values():
            processed_files.extend(file_list)
        logger.info(f"Files processed: {len(processed_files)} file(s) - {processed_files}")
        if file_handler.text_contents:
            input += "\n\n" + "\n\n".join(file_handler.text_contents)
            logger.info(f"Text contents added to input: {len(file_handler.text_contents)} text(s)")

    if origin == Origin.DISCORD and message.guild:
        bot_user = bot.user if bot else None
        if bot_user:
            mention_str = f"<@{bot_user.id}>"
            input = input.replace(mention_str, "").strip()

    if model == "auto":
        logger.info("Auto-selecting model...")
        selector = LLMSelector()
        selected_model = await selector.select_model(input)
        if selected_model.lower() in AVAILABLE_MODELS:
            model = selected_model.lower()
            logger.info(f"Model auto-selected: {model}")
        else:
            model = Model.LLAMA.value
            logger.info(f"No suitable model found, defaulting to: {model}")
    
    if origin == Origin.DISCORD:
        parameters = RequestParameters()
        
        query = input
        while True:
            command_found = False
            
            model_match = re.search(r' -m\s+([^\s]+)$', query)
            if model_match:
                model_name = model_match.group(1)
                if model_name.lower() in AVAILABLE_MODELS:
                    parameters.model = model_name
                    query = query[:model_match.start()].rstrip()
                    logger.info(f"Model specified: {model_name}")
                    command_found = True
            
            elif query.endswith(" -h"):
                query = query[:-3].rstrip()
                parameters.history = False
                logger.info("History disabled")
                command_found = True
            elif query.endswith(" -p"):
                query = query[:-3].rstrip()
                parameters.preprompt = False
                logger.info("Preprompt disabled")
                command_found = True
            elif query.endswith(" -t"):
                query = query[:-3].rstrip()
                parameters.tools = False
                logger.info("Tools disabled")
                command_found = True
            elif query.endswith(" +i"):
                query = query[:-3].rstrip()
                parameters.internet = True
                logger.info("Internet enabled")
                command_found = True
            elif query.endswith(" +a"):
                query = query[:-3].rstrip()
                parameters.audio = True
                logger.info("Audio enabled")
                command_found = True
            elif query.endswith(" +r"):
                query = query[:-3].rstrip()
                parameters.raw = True
                logger.info("Raw mode enabled")
                command_found = True
            
            if not command_found:
                break

        logger.info(f"Query: {query}")
        if not query or query.isspace():
            logger.info(f"Empty message from {user.id}")
            query = "Hi! Please ask me a question."
            
    memory_manager = None
    if use_memory:
        memory_manager = await get_memory_manager()
        
    relevant_memories = await memory_manager.get_hybrid_memories(
        user_id, conv_id, input, recent_limit=4, similar_limit=5
    )

    for mem_list in relevant_memories.values():
        for mem in mem_list:
            if 'content' not in mem or mem['content'] is None:
                mem['content'] = mem.get('text', '')

    history = []
    if relevant_memories.get('stm'):
        for mem in relevant_memories.get('stm', []):
            role = "user" if mem['role'] == "user" else "assistant"
            history.append({"role": role, "content": mem.get('content')})

    system_prompt = read_file("configs/prompts/api_prompt.txt") if origin == Origin.API else read_file("configs/prompts/discord_prompt.txt")
    system_prompt = system_prompt.format(
        date=datetime.datetime.now().strftime('%Y-%b-%d-%a'),
        time=datetime.datetime.now().strftime('%H:%M:%S')
    ) if origin == Origin.API else system_prompt.format(
        date=datetime.datetime.now().strftime('%Y-%b-%d-%a'),
        time=datetime.datetime.now().strftime('%H:%M:%S'),
        user=user.display_name
    )
    if relevant_memories.get('ltm'):
        system_prompt += f"""
        \n**User's system prompt:**
        {'\n'.join([mem.get('content') for mem in relevant_memories.get('ltm', [])])}"""

    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": input}]
    from utils.ai_process.chat_model import ChatModel
    from utils.ai_process.base_chat_model import ChatParameters
    chat_model = ChatModel(model)
    chat_params = ChatParameters(messages=messages, temperature=0.7, stream=stream, raw=True, files=processed_files)
    
    if stream:
        async for chunk in chat_model.chat(chat_params):
            yield chunk
    else:
        result = await chat_model.chat(chat_params)
        
        logger.info(f"Réponse générée - Modèle: {result.model}, Usage: {result.usage} tokens, Temps: {result.elapsed_time}")
        logger.debug(f"Contenu de la réponse: {result.response}...")
        logger.info(f"Réponse envoyée à {user.display_name}")
            
        if use_memory:
            await memory_manager.add_conversation_message(user_id, conv_id, input, "user")
            await memory_manager.add_conversation_message(user_id, conv_id, result.response, "assistant")
            
            stm_memories = await memory_manager.get_memories(user_id, conv_id, limit_stm=300, limit_ltm=0)
            stm_list = stm_memories.get('stm', [])
            if len(stm_list) > 3:
                older_messages = stm_list[:-3]
                dialogue = ""
                for mem in older_messages:
                    role = mem.get('role', 'user')
                    content = mem.get('content') or mem.get('text', '')
                    dialogue += f"{role.capitalize()}: {content}\n"
                try:
                    summary = summarize(dialogue)
                    await memory_manager.add_long_term_memory(user_id, conv_id, "Conversation Summary", summary, "conversation")
                    old_ids = [mem['id'] for mem in older_messages]
                    await memory_manager.delete_stm_memories(old_ids)
                    logger.info(f"Summarized {len(older_messages)} old messages into LTM")
                except Exception as e:
                    logger.error(f"Failed to summarize and store in LTM: {e}")
        
        yield result