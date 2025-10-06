import logging
from utils.config import LOGGER_NAME
#from temp.speech_gen import send_voice_message
from utils.user_config import get_audio_gen_active, get_audio_voice
from utils.ai_utils import generate_response
from utils.table_converter import detect_and_convert_tables
from utils.audio_gen import send_voice_message
import discord
import io
import json
import re

logger = logging.getLogger(LOGGER_NAME)

MODELS_LIST = [
    "mistral",
    "openai", 
    "claude",
    "llama",
    "deepseek",
    "qwen",
    "gemini", 
    "grok",
    "perplexity",
    "cohere",
    "evilgpt",
    "glm",
    "kimi", 
    "phi"
]

async def process_ai_response(bot, query, message):
    try:
        parameters = {
            "history": True, 
            "preprompt": True, 
            "tools": False, 
            "internet": False, 
            "audio" : False,
            "raw": False,
            "model": bot.user.id if isinstance(bot, discord.Client) else bot.id
        }

        while True:
            command_found = False
            
            model_match = re.search(r' -m \{([^}]+)\}$', query)
            if model_match:
                model_name = model_match.group(1)
                if model_name.lower() in MODELS_LIST:
                    parameters["model"] = model_name
                    query = query[:model_match.start()].rstrip()
                    logger.info(f"Modèle spécifié via commande: {model_name}")
                    command_found = True
                else:
                    logger.warning(f"Modèle spécifié inconnu: {model_name}")
            elif query.endswith(" -h"):
                query = query[:-3].rstrip()
                parameters["history"] = False
                logger.info("Historique désactivé via commande")
                command_found = True
            elif query.endswith(" -p"):
                query = query[:-3].rstrip()
                parameters["preprompt"] = False
                logger.info("Preprompt désactivé via commande")
                command_found = True
            elif query.endswith(" -t"):
                query = query[:-3].rstrip()
                parameters["tools"] = False
                logger.info("Outils désactivés via commande")
                command_found = True
            elif query.endswith(" +i"):
                query = query[:-3].rstrip()
                parameters["internet"] = True
                logger.info("Internet activé via commande")
                command_found = True
            elif query.endswith(" +a"):
                query = query[:-3].rstrip()
                parameters["audio"] = True
                logger.info("Audio activé via commande")
                command_found = True
            elif query.endswith(" +r"):
                query = query[:-3].rstrip()
                parameters["raw"] = True
                logger.info("Mode raw activé via commande")
                command_found = True
            
            if not command_found:
                break

        logger.info(f"Message : {query}")
        if not query or query.isspace():
            logger.info(f"Message vide reçu de {message.author.id}")
            query = "Hi ! (Tell the user to mention you (<@1286951908786962442>))"

        logger.debug(f"Query processed: {query}")
        try:
            response = await generate_response(
                user_id=int(message.author.id),
                server_id=int(message.channel.id if not message.guild else message.guild.id),
                raw_content=query,
                attachments=message.attachments,
                bot=bot,
                user=message.author.display_name,
                parameters=parameters
            )
            logger.debug(f"Réponse générée avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse : {e}")
            await message.channel.send("Une erreur s'est produite lors de la génération de la réponse.")
            return

        # Extract response text properly
        if isinstance(response, dict) and 'response' in response:
            response_text = response['response']
        elif isinstance(response, str):
            response_text = response
        else:
            logger.error(f"Type de réponse non géré : {type(response)}")
            await message.channel.send("Une erreur s'est produite lors de la génération de la réponse.")
            return
            
        # Send using correct format (image/text)
        try:
            if isinstance(response_text, bytes):
                await message.channel.send(file=discord.File(io.BytesIO(response_text), filename="image.png"))
            elif isinstance(response_text, str):
                response_text = detect_and_convert_tables(response_text)
                
                await smart_long_messages(message.channel, response_text)
                logger.debug(f"Réponse envoyée avec succès.")
            else:
                logger.error(f"Type de réponse texte non géré : {type(response_text)}")
                await message.channel.send("Une erreur s'est produite lors de la génération de la réponse.")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message : {e}")
            await message.channel.send("Une erreur s'est produite lors de l'envoi du message.")

        # Audio generation if enabled by command `+a`
        try:
            if parameters.get("audio", False):
                await send_voice_message(message.channel, response_text)
                logger.debug(f"Voice message sent successfully.")
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la voix : {e}")
            await message.channel.send("Une erreur s'est produite lors de la génération de la voix.")

    except Exception as e:
        logger.error(f"Erreur lors de la génération : {e}")
        await message.channel.send("Une erreur s'est produite lors de la génération.")

async def smart_long_messages(channel, response, max_length: int = 2000):
    """
    Sends a long message to Discord, preserving code blocks and never splitting inside a code block.
    """

    pattern = re.compile(r"(```[\s\S]*?```)")
    parts = pattern.split(response)
    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            await send_code_block(channel, part, max_length)
        else:
            await send_text_in_chunks(channel, part, max_length)

async def send_text_in_chunks(channel, text: str, max_length: int = 2000):
    """
    Sends plain text in chunks, never breaking lines in the middle if possible.
    """
    lines = text.splitlines(keepends=True)
    current_message = ""
    for line in lines:
        if len(current_message) + len(line) > max_length:
            if current_message:
                await channel.send(current_message.rstrip())
            current_message = ""
        current_message += line
    if current_message.strip():
        await channel.send(current_message.rstrip())

async def send_code_block(channel, code_block: str, max_length: int = 2000):
    """
    Sends a code block, splitting into multiple code blocks if needed but never breaking a line of code.
    """
    first_line_end = code_block.find('\n')
    if first_line_end == -1:
        language = ""
        code = code_block[3:-3]
    else:
        language = code_block[3:first_line_end].strip()
        code = code_block[first_line_end+1:-3]

    code_lines = code.splitlines(keepends=True)
    code_prefix = f"```{language}\n" if language else "```"
    code_suffix = "```"
    current_code = code_prefix
    for line in code_lines:
        if len(current_code) + len(line) + len(code_suffix) > max_length:
            current_code += code_suffix
            await channel.send(current_code)
            current_code = code_prefix
        current_code += line
    if current_code.strip() != code_prefix.strip():
        current_code += code_suffix
        await channel.send(current_code)