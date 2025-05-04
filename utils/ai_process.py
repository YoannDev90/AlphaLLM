#ai_process.py

import logging
from utils.md_converter import md_conversion
from utils.langs import get_translation
#from utils.roles_utils import get_model_from_role
from utils.speech_gen import send_voice_message
from utils.web_process import get_text_from_url
from utils.user_config import get_def_model, get_audio_gen_active, get_audio_voice
from utils.user_manager import new_interaction, new_query
from utils.ai_utils import generate_response
import re

logger = logging.getLogger('AlphaLLM')
URL_REGEX = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+\/?(?:\S*)'

async def process_ai_response(message):
    try:
        logger.info(f"Bot mentionné par {message.author.display_name} ({message.author.id})")
        logger.debug(f"Bot mentionné par {message.author.display_name} ({message.author.id})")
        new_query(message.author.id)
        new_interaction(message.author.id)
        mentioned_roles = [role for role in message.role_mentions if role in message.guild.me.roles]
        selected_role = mentioned_roles[0] if mentioned_roles else None
        model_name = "cerebras"
        model_name = get_def_model(message.author.id) if get_def_model(message.author.id) else model_name
        logger.debug(f"Model name selected: {model_name}")
        # if selected_role:
        #     model_name = get_model_from_role(message.guild.id, selected_role.id)
        #     if not model_name:
        #         await message.channel.send(
        #             f"Le rôle `{selected_role.name}` n'a pas de modèle associé. "
        #             f"Veuillez utiliser la commande `/models` pour configurer un modèle."
        #         )
        #         return

        query = message.content.replace(f"<@{message.guild.me.id}>", "").strip()
        logger.debug(f"Query received: {query}")
        if not query:
            await message.channel.send("Veuillez poser une question ou faire une demande.")
            return

        try:
            response = await generate_response(
                user_id=int(message.author.id),
                server_id=int(message.guild.id),
                raw_content=query,
                attachments=message.attachments,
                model_name=model_name
            )
            logger.debug(f"Response generated successfully.")
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse : {e}")
            await message.channel.send("Une erreur s'est produite lors de la génération de la réponse.")
            return

        try:
            await smart_long_messages(message.channel, response)
            logger.debug(f"Response sent successfully.")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message : {e}")
            await message.channel.send("Une erreur s'est produite lors de l'envoi du message.")

        # try:
        #     if get_audio_gen_active(message.author.id):
        #         logger.debug(f"Audio generation is active for user {message.author.id}.")
        #         await send_voice_message(message.channel, response, get_audio_voice(message.author.id))
        #         logger.debug(f"Voice message sent successfully.")
        # except Exception as e:
        #     logger.error(f"Erreur lors de la génération de la voix : {e}")
        #     logger.error(f"Error generating voice message: {e}")
        #     await message.channel.send("Une erreur s'est produite lors de la génération de la voix.")
    except Exception as e:
        logger.error(f"Erreur lors de la génération : {e}")
        await message.channel.send("Une erreur s'est produite lors de la génération.")

async def smart_long_messages(channel, text: str, max_length: int = 2000):
    """
    Sends a long message to Discord, preserving code blocks and never splitting inside a code block.
    """
    # Pattern to split on code blocks (captures the ```lang\n...```
    pattern = re.compile(r"(```[\s\S]*?```)")
    parts = pattern.split(text)
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
    # Extract the language (if any)
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
        # +3 for closing ```
        if len(current_code) + len(line) + len(code_suffix) > max_length:
            current_code += code_suffix
            await channel.send(current_code)
            current_code = code_prefix
        current_code += line
    if current_code.strip() != code_prefix.strip():
        current_code += code_suffix
        await channel.send(current_code)