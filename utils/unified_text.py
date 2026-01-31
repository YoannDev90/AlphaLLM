import datetime
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from config import (AVAILABLE_MODELS, LOGGER_NAME, MAX_CONVERSATION_HISTORY,
                    MAX_LTM_RESULTS, MODELS_OWNERS, read_file)
from utils.ai_process.ai_utils import summarize
from utils.ai_process.llm_selector import LLMSelector
from utils.discord_utils.permission_checker import PermissionChecker
from utils.discord_utils.status import (update_status_on_failure,
                                        update_status_on_success)
from utils.function_calling import get_function_caller
from utils.handlers.files import FileHandler
from utils.memory import get_memory_manager, initialize_memory_manager

logger = logging.getLogger(LOGGER_NAME)
perms_checker = PermissionChecker()


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
Origin.STATUS_CHECK = Origin("status_check")


class Text_Model(Enum):
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


async def unified_text_gen(
    user_id: int,
    conv_id: str,
    input: str,
    model: Union[str, Text_Model],
    files: Optional[List[Any]] = None,
    origin: Optional[Origin] = None,
    message: Optional[Any] = None,
    bot: Optional[Any] = None,
    stream: bool = False,
    use_memory: bool = True,
):
    """
    Fonction pour gérer les requêtes vers les modèles, avec permissions, mémoire, pré/post-traitement et erreurs.

    Args:
        user_id: ID de l'utilisateur.
        conv_id: ID de la conversation.
        input: Texte d'entrée de l'utilisateur.
        model: Modèle à utiliser (e.g., 'claude' or Text_Model.CLAUDE).
        files: Liste des fichiers attachés (optionnel).
        origin: Origine de la requête (API ou Discord, via Origin).
        message: Message supplémentaire pour Discord (optionnel).
        bot: Bot supplémentaire pour Discord (optionnel).
        stream: Si True, streaming de la réponse.
        use_memory: Si True, utilise la mémoire. (API seulement)
    """
    logger.debug(
        f"Entered unified_text_gen with user_id={user_id}, conv_id={conv_id}, input='{input}', model={model}, stream={stream}"
    )
    origin = origin or Origin.API
    model = model or Text_Model.AUTO.value
    if isinstance(model, Text_Model):
        model = model.value

    from utils.ai_process.base_chat_model import ChatParameters, ChatResult
    from utils.ai_process.chat_model import ChatModel

    user = None
    if origin == Origin.DISCORD:
        user = (
            message.author
            if hasattr(message, "author")
            else message.user if message else None
        )
        logger.debug(
            f"Utilisateur: {user.display_name if user else user_id}, "
            f"Modèle: {model}, Origine: {origin}, "
            f"Fichiers: {len(files) if files else 0}"
        )

    file_handler = None
    processed_files = []
    if files:
        logger.info(f"Files uploaded: {len(files)} file(s) - {[str(f) for f in files]}")
        file_handler = FileHandler(files)
        await file_handler.process_files()
        for file_list in file_handler.saved_files.values():
            processed_files.extend(file_list)
        logger.info(
            f"Files processed: {len(processed_files)} file(s) - {processed_files}"
        )
        if file_handler.text_contents:
            input += "\n\n" + "\n\n".join(file_handler.text_contents)
            logger.info(
                f"Text contents added to input: {len(file_handler.text_contents)} text(s)"
            )

    if origin == Origin.DISCORD and message.guild:
        bot_user = bot.user if bot else None
        if bot_user:
            mention_str = f"<@{bot_user.id}>"
            input = input.replace(mention_str, "").strip()

    if origin == Origin.DISCORD:
        parameters = RequestParameters()

        query = input
        while True:
            command_found = False

            model_match = re.search(r" -m\s+([^\s]+)$", query)
            if model_match:
                model_name = model_match.group(1)
                if model_name.lower() in AVAILABLE_MODELS:
                    parameters.model = model_name
                    query = query[: model_match.start()].rstrip()
                    logger.info(f"Model specified: {model_name}")
                    command_found = True

            elif query.endswith(" -h"):
                query = query[:-3].rstrip()
                parameters.history = False
                logger.info("History disabled")
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

            if not command_found:
                break

        logger.info(f"Query: {query}")
        if not query or query.isspace():
            user_name = user.display_name if user else f"user_{user_id}"
            logger.info(f"Empty message from {user_name}")
            query = "Hi! Please ask me a question."

        if parameters.model:
            model = parameters.model

    if not origin == Origin.STATUS_CHECK:
        function_caller = await get_function_caller()
        tool_calls = function_caller.check_for_tools(input)
        if tool_calls:
            logger.info(f"Tool calls detected: {tool_calls}")
            tool_responses = []
            for call in tool_calls:
                func_name = call["function"]
                params = call["parameters"]
                from utils.function_calling.tools import execute_tool

                response = await execute_tool(func_name, params)
                if response is None or response.startswith("error"):
                    break
                tool_responses.append(response)
            tool_response = "\n".join(tool_responses)
            if stream:
                from utils.ai_process.base_chat_model import StreamChunk

                yield StreamChunk(
                    chunk=tool_response,
                    done=True,
                    response=tool_response,
                    usage=0,
                    model="function_calling",
                    elapsed_time="0.0s",
                )
            else:
                from utils.ai_process.base_chat_model import ChatResult

                result = ChatResult(
                    response=tool_response,
                    usage=0,
                    model="function_calling",
                    elapsed_time="0.0s",
                )
                yield result
            return

    if model == "auto":
        logger.info("Auto-selecting model...")
        selector = LLMSelector()
        selected_model = await selector.select_model(input)
        if selected_model.lower() in AVAILABLE_MODELS:
            model = selected_model.lower()
            logger.debug(f"Model auto-selected: {model}")

    if model not in AVAILABLE_MODELS:
        model = Text_Model.LLAMA.value
        logger.debug(f"Model not available, defaulting to: {model}")

    logger.debug(f"Final model to use: {model}")
    logger.debug("About to initialize memory manager")
    memory_manager = None
    if use_memory:
        memory_manager = await get_memory_manager()
        logger.debug("Memory manager initialized")

    relevant_memories = {"stm": [], "ltm": []}
    if use_memory and memory_manager:
        logger.debug("About to fetch STM memories using get_conversation_messages")
        stm_messages = await memory_manager.get_conversation_messages(
            user_id, conv_id, limit=MAX_CONVERSATION_HISTORY
        )
        relevant_memories["stm"] = stm_messages
        logger.debug(f"Fetched {len(stm_messages)} STM memories")

        logger.debug("About to fetch LTM memories using search_memories")
        ltm_texts = await memory_manager.search_memories(input, top_k=MAX_LTM_RESULTS)
        relevant_memories["ltm"] = [{"content": text} for text in ltm_texts]
        logger.debug(f"Fetched {len(ltm_texts)} LTM memories")
    logger.debug("Relevant memories fetched")

    logger.debug("About to process relevant memories")
    for mem_list in relevant_memories.values():
        for mem in mem_list:
            if "content" not in mem or mem["content"] is None:
                mem["content"] = mem.get("text", "")

    logger.debug("Processed relevant memories to ensure 'content' field is populated")

    history = []
    if relevant_memories.get("stm"):
        for mem in relevant_memories.get("stm", []):
            role = "user" if mem["role"] == "user" else "assistant"
            history.append({"role": role, "content": mem.get("content")})

    logger.debug(f"Conversation history prepared with {len(history)} messages")
    logger.debug(f"Input prepared for model: {input}")

    system_prompt = ""
    if model == Text_Model.EVILGPT.value:
        try:
            system_prompt = read_file("configs/prompts/evilgpt_prompt.txt")
        except Exception as e:
            logger.error(f"Failed to read EvilGPT prompt file: {e}")
    if origin == Origin.API:
        try:
            system_prompt += read_file("configs/prompts/api_prompt.txt")
        except Exception as e:
            logger.error(f"Failed to read API prompt file: {e}")
    elif origin == Origin.STATUS_CHECK:
        try:
            system_prompt += read_file("configs/prompts/status_prompt.txt")
        except Exception as e:
            logger.error(f"Failed to read status prompt file: {e}")
    else:
        try:
            system_prompt += read_file("configs/prompts/discord_prompt.txt")
        except Exception as e:
            logger.error(f"Failed to read Discord prompt file: {e}")

    logger.debug(f"Base system prompt loaded {system_prompt}...")

    user_name = (
        user.display_name if origin == Origin.DISCORD and user else f"User_{user_id}"
    )
    owner = MODELS_OWNERS.get(model, "Unknown")
    logger.debug(f"User: {user_name}, ID: {user.id if user else user_id}")
    logger.debug(f"Model owner: {owner}")

    try:
        if origin == Origin.API or origin == Origin.STATUS_CHECK:
            system_prompt = system_prompt.format(
                date=datetime.datetime.now().strftime("%Y-%b-%d-%a"),
                time=datetime.datetime.now().strftime("%H:%M:%S"),
                model=model,
                owner=owner,
            )
        else:
            system_prompt = system_prompt.format(
                date=datetime.datetime.now().strftime("%Y-%b-%d-%a"),
                time=datetime.datetime.now().strftime("%H:%M:%S"),
                user=user_name,
                model=model,
                owner=owner,
            )
    except Exception as e:
        logger.error(f"Error formatting system prompt: {e}")

    logger.debug(f"System prompt prepared for model: {system_prompt}...")

    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": input}]
    )

    logger.debug("Messages prepared for chat")
    chat_model = ChatModel(model)
    logger.debug("ChatModel instance created")
    chat_params = ChatParameters(
        messages=messages,
        model=model,
        temperature=0.7,
        stream=stream,
        raw=True,
        files=processed_files,
    )
    logger.debug("ChatParameters created")

    logger.debug("About to call chat_model.chat")
    if stream:
        async for chunk in chat_model.chat(chat_params):
            yield chunk
    else:
        logger.debug("Calling await chat_model.chat for non-stream")
        result = await chat_model.chat(chat_params)
        logger.debug("Chat result received")

        # Only update status on success if we got a real response (not an error message)
        error_messages = [
            "Request timed out",
            "I'm sorry, but I couldn't generate a response",
            "API configuration error",
            "Request timed out after trying all available models"
        ]
        is_error_response = any(error_msg in result.response for error_msg in error_messages)

        if not is_error_response:
            update_status_on_success(model, result.elapsed_time)
        else:
            update_status_on_failure(model)

        logger.info(
            f"Réponse générée - Modèle: {result.model}, Usage: {result.usage} tokens, Temps: {result.elapsed_time}"
        )
        logger.debug(f"Contenu de la réponse: {result.response}...")

        if use_memory and memory_manager:
            await memory_manager.store_conversation_message(
                user_id, conv_id, input, "user"
            )
            await memory_manager.store_conversation_message(
                user_id, conv_id, result.response, "assistant"
            )

            stm_list = await memory_manager.get_conversation_messages(
                user_id, conv_id, limit=300
            )
            if len(stm_list) > 3:
                older_messages = stm_list[:-3]
                dialogue = ""
                for mem in older_messages:
                    role = mem.get("role", "user")
                    content = mem.get("content") or mem.get("text", "")
                    dialogue += f"{role.capitalize()}: {content}\n"
                try:
                    summary = summarize(dialogue)
                    await memory_manager.add_memory(
                        f"{user_id}_{conv_id}_summary_{len(stm_list)}",
                        summary,
                        {
                            "type": "conversation",
                            "user_id": user_id,
                            "conv_id": conv_id,
                        },
                    )
                    await memory_manager.delete_stm_messages(
                        [msg.doc_id for msg in older_messages]
                    )
                    logger.info(
                        f"Summarized {len(older_messages)} old messages into LTM"
                    )
                except Exception as e:
                    logger.error(f"Failed to summarize and store in LTM: {e}")

        yield result
