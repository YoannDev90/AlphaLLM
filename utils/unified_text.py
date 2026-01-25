import datetime
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from config import AVAILABLE_MODELS, MODELS_OWNERS, LOGGER_NAME, read_file, PROMPT_DIR, EVILGPT_PROMPT_PATH, API_PROMPT_PATH, STATUS_PROMPT_PATH, DISCORD_PROMPT_PATH, MAX_FILE_SIZE, ALLOWED_MIME_TYPES
from utils.discord_utils.status import update_status_on_success, update_status_on_failure
from utils.ai_process.ai_utils import summarize
from utils.ai_process.llm_selector import LLMSelector
from utils.discord_utils.permission_checker import PermissionChecker
from utils.handlers.files import FileHandler
from utils.memory import get_memory_manager, initialize_memory_manager
from utils.function_calling import get_function_caller
from utils.ai_process.base_chat_model import ChatParameters, ChatResult, StreamChunk
from utils.ai_process.chat_model import ChatModel

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
    """Class to define the origin of the request with additional attributes for DISCORD."""
    
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
    """Enum to define available models."""
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


def validate_inputs(user_id: int, model: Union[str, Text_Model], files: Optional[List[Any]] = None) -> None:
    """
    Validate input parameters for the unified_text_gen function.

    Args:
        user_id: User ID, must be a non-negative integer.
        model: Model name or Text_Model enum.
        files: List of files, optional.

    Raises:
        ValueError: If validation fails.
    """
    if not isinstance(user_id, int) or user_id < 0:
        raise ValueError("user_id must be a non-negative integer.")
    
    if isinstance(model, Text_Model):
        model = model.value
    if model not in AVAILABLE_MODELS and model != "auto":
        raise ValueError(f"Invalid model: {model}. Must be one of {list(AVAILABLE_MODELS)} or 'auto'.")
    
    if files:
        for file in files:
            if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
                raise ValueError(f"File {file.filename if hasattr(file, 'filename') else 'unknown'} exceeds maximum size of {MAX_FILE_SIZE} bytes.")
            if hasattr(file, 'content_type') and file.content_type not in ALLOWED_MIME_TYPES:
                raise ValueError(f"File type {file.content_type} not allowed. Allowed types: {ALLOWED_MIME_TYPES}")


def parse_discord_parameters(input: str) -> tuple[str, RequestParameters]:
    """
    Parse Discord-specific parameters from the input string.

    Args:
        input: The input string to parse.

    Returns:
        Tuple of (cleaned_query, parameters).
    """
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
    return query, parameters


async def handle_file_processing(files: Optional[List[Any]] = None) -> tuple[Optional[FileHandler], List[str]]:
    """
    Process uploaded files.

    Args:
        files: List of files to process.

    Returns:
        Tuple of (file_handler, processed_files).
    """
    if not files:
        return None, []
    
    logger.info(f"Files uploaded: {len(files)} file(s) - {[str(f) for f in files]}")
    file_handler = FileHandler(files)
    await file_handler.process_files()
    processed_files = []
    for file_list in file_handler.saved_files.values():
        processed_files.extend(file_list)
    logger.info(f"Files processed: {len(processed_files)} file(s) - {processed_files}")
    if file_handler.text_contents:
        input_with_text = "\n\n" + "\n\n".join(file_handler.text_contents)
        logger.info(f"Text contents added to input: {len(file_handler.text_contents)} text(s)")
    else:
        input_with_text = ""
    return file_handler, processed_files, input_with_text


def prepare_messages_and_prompt(system_prompt: str, history: List[Dict[str, str]], input: str) -> List[Dict[str, str]]:
    """
    Prepare the messages list for the model call.

    Args:
        system_prompt: The system prompt.
        history: Conversation history.
        input: User input.

    Returns:
        List of messages.
    """
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": input}]
    return messages


async def execute_model_call(chat_model: ChatModel, chat_params: ChatParameters, stream: bool):
    """
    Execute the model call, handling streaming or non-streaming.

    Args:
        chat_model: The chat model instance.
        chat_params: Parameters for the chat.
        stream: Whether to stream the response.

    Yields:
        StreamChunk or ChatResult.
    """
    if stream:
        async for chunk in chat_model.chat(chat_params):
            yield chunk
    else:
        result = await chat_model.chat(chat_params)
        update_status_on_success(chat_params.model, result.elapsed_time)
        logger.info(f"Response generated - Model: {result.model}, Usage: {result.usage} tokens, Time: {result.elapsed_time}")
        logger.debug(f"Response content: {result.response}...")
        yield result


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
        use_memory: bool = True
    ):
    """
    Unified function to handle text generation requests, with permissions, memory, pre/post-processing, and error handling.

    Args:
        user_id: User ID.
        conv_id: Conversation ID.
        input: User's input text.
        model: Model to use (e.g., 'claude' or Text_Model.CLAUDE).
        files: List of attached files (optional).
        origin: Request origin (API or Discord, via Origin).
        message: Additional message for Discord (optional).
        bot: Additional bot for Discord (optional).
        stream: If True, stream the response.
        use_memory: If True, use memory (API only).
    """
    # Validate inputs
    validate_inputs(user_id, model, files)
    
    origin = origin or Origin.API
    model = model or Text_Model.AUTO.value
    if isinstance(model, Text_Model):
        model = model.value

    user = None
    if origin == Origin.DISCORD:
        user = message.author if hasattr(message, 'author') else message.user if message else None
        logger.debug(f"User: {user.display_name if user else user_id}, "
                    f"Model: {model}, Origin: {origin}, "
                    f"Files: {len(files) if files else 0}")

    # Handle file processing
    file_handler, processed_files, input_text_addition = await handle_file_processing(files)
    if input_text_addition:
        input += input_text_addition

    if origin == Origin.DISCORD:
        bot_user = bot.user if bot else None
        if bot_user:
            mention_str = f"<@{bot_user.id}>"
            input = input.replace(mention_str, "").strip()

    # Parse Discord parameters
    if origin == Origin.DISCORD:
        input, parameters = parse_discord_parameters(input)
        if parameters.model:
            model = parameters.model
        if not input or input.isspace():
            user_name = user.display_name if user else f"user_{user_id}"
            logger.info(f"Empty message from {user_name}")
            input = "Hi! Please ask me a question."

    # Handle function calling for Discord
    if origin == Origin.DISCORD:
        function_caller = await get_function_caller()
        tool_calls = function_caller.check_for_tools(input)
        if tool_calls:
            logger.info(f"Tool calls detected: {tool_calls}")
            tool_responses = []
            for call in tool_calls:
                func_name = call['function']
                params = call['parameters']
                from utils.function_calling.tools import execute_tool
                response = await execute_tool(func_name, params)
                if response is None or response.startswith("error"):
                    break
                tool_responses.append(response)
            tool_response = "\n".join(tool_responses)
            if stream:
                yield StreamChunk(chunk=tool_response, done=True, response=tool_response, usage=0, model="function_calling", elapsed_time="0.0s")
            else:
                result = ChatResult(response=tool_response, usage=0, model="function_calling", elapsed_time="0.0s")
                yield result
            return

    # Auto-select model if needed
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
            
    logger.debug(f"Final model to use: {model.capitalize()}")

    # Handle memory
    history = []
    memory_manager = None
    if use_memory:
        try:
            memory_manager = await get_memory_manager()
            if memory_manager:
                relevant_memories = await memory_manager.get_hybrid_memories(
                    user_id, conv_id, input, recent_limit=4, similar_limit=5
                )
            else:
                relevant_memories = {'stm': [], 'ltm': []}
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            relevant_memories = {'stm': [], 'ltm': []}  # Fallback to no memory

        logger.debug(f"Relevant memories fetched: "
                    f"STM: {len(relevant_memories.get('stm', []))}, "
                    f"LTM: {len(relevant_memories.get('ltm', []))}")

        for mem_list in relevant_memories.values():
            for mem in mem_list:
                if 'content' not in mem or mem['content'] is None:
                    mem['content'] = mem.get('text', '')

        logger.debug("Processed relevant memories to ensure 'content' field is populated")

        if relevant_memories.get('stm'):
            for mem in relevant_memories.get('stm', []):
                role = "user" if mem['role'] == "user" else "assistant"
                history.append({"role": role, "content": mem.get('content')})

        logger.debug(f"Conversation history prepared with {len(history)} messages")
        logger.debug(f"Input prepared for model: {input}")

    # Prepare system prompt
    system_prompt = ""
    if model == Text_Model.EVILGPT.value:
        try:
            system_prompt = read_file(EVILGPT_PROMPT_PATH)
        except Exception as e:
            logger.error(f"Failed to read EvilGPT prompt file: {e}")
    if origin == Origin.API:
        try:
            system_prompt += read_file(API_PROMPT_PATH)
        except Exception as e:
            logger.error(f"Failed to read API prompt file: {e}")
    elif origin == Origin.STATUS_CHECK:
        try:
            system_prompt += read_file(STATUS_PROMPT_PATH)
        except Exception as e:
            logger.error(f"Failed to read status prompt file: {e}")
    else:
        try:
            system_prompt += read_file(DISCORD_PROMPT_PATH)
        except Exception as e:
            logger.error(f"Failed to read Discord prompt file: {e}")
    
    user_name = user.display_name if origin == Origin.DISCORD and user else f"User_{user_id}"
    owner = MODELS_OWNERS.get(model, "Unknown")
    logger.debug(f"User: {user_name}, ID: {user.id if user else user_id}")

    try:
        if origin == Origin.API or origin == Origin.STATUS_CHECK:
            system_prompt = system_prompt.format(
                date=datetime.datetime.now().strftime('%Y-%b-%d-%a'),
                time=datetime.datetime.now().strftime('%H:%M:%S'),
                model=model.capitalize(),
                owner=owner
            )
        else:
            system_prompt = system_prompt.format(
                date=datetime.datetime.now().strftime('%Y-%b-%d-%a'),
                time=datetime.datetime.now().strftime('%H:%M:%S'),
                user=user_name,
                model=model.capitalize(),
                owner=owner
            )
    except Exception as e:
        logger.error(f"Error formatting system prompt: {e}")

    logger.debug(f"System prompt prepared for model: {system_prompt}...")

    # Prepare messages
    messages = prepare_messages_and_prompt(system_prompt, history, input)
    
    chat_model = ChatModel(model)
    chat_params = ChatParameters(messages=messages, model=model, temperature=0.7, stream=stream, raw=True, files=processed_files)
    
    # Execute model call
    async for result in execute_model_call(chat_model, chat_params, stream):
        yield result
        
    # Handle memory storage if not streaming
    if not stream and use_memory and memory_manager:
        try:
            await memory_manager.add_conversation_message(user_id, conv_id, input, "user")
            await memory_manager.add_conversation_message(user_id, conv_id, result.response, "assistant")
            
            stm_memories = await memory_manager.get_memories(user_id, conv_id, limit_stm=300, limit_ltm=0)
            stm_list = stm_memories.get('stm', [])
            if len(stm_list) > 3:
                older_messages = stm_list[:-3]
                old_ids = [mem['id'] for mem in older_messages]
                await memory_manager.delete_stm_memories(old_ids)
                logger.info(f"Deleted {len(older_messages)} old messages from STM")
        except Exception as e:
            logger.error(f"Failed to store memories: {e}")