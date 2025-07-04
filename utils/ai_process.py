import logging
#from temp.speech_gen import send_voice_message
from utils.user_config import get_audio_gen_active, get_audio_voice
from utils.user_manager import new_interaction, new_query
from utils.ai_utils import generate_response
from utils.table_converter import detect_and_convert_tables
import discord
import io
import re

logger = logging.getLogger('AlphaLLM')

async def process_ai_response(bot,message):
    try:
        logger.info(f"Bot mentionné par {message.author.display_name} ({message.author.id})")
        new_query(message.author.id)
        new_interaction(message.author.id)

        bot_mention = f"<@{bot.user.id}>"

        query = message.content.replace(bot_mention, "").strip()
        parameters = {"history": True, "preprompt": True, "tools": True}

        while True:
            if query.endswith(" -h"):
                query = query[:-3].rstrip()
                parameters["history"] = False
            elif query.endswith(" -p"):
                query = query[:-3].rstrip()
                parameters["preprompt"] = False
            elif query.endswith(" -t"):
                query = query[:-3].rstrip()
                parameters["tools"] = False
            else:
                break


        logger.info(f"Message : {query}")
        if not query or query.isspace():
            logger.warning(f"Empty query from {message.author.display_name}")
            await message.channel.send("Veuillez poser une question ou faire une demande.")
            return

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

        try:
            # Convertir les tableaux Markdown en tableaux ASCII
            response = detect_and_convert_tables(response)
            await smart_long_messages(message.channel, response)
            logger.debug(f"Réponse envoyée avec succès.")
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
        #     await message.channel.send("Une erreur s'est produite lors de la génération de la voix.")
    except Exception as e:
        logger.error(f"Erreur lors de la génération : {e}")
        await message.channel.send("Une erreur s'est produite lors de la génération.")

async def smart_long_messages(channel, response, max_length: int = 2000):
    """
    Sends a long message to Discord, preserving code blocks and never splitting inside a code block.
    """
    if isinstance(response, bytes):
        # Envoi direct des données binaires comme fichier
        await channel.send(file=discord.File(io.BytesIO(response), filename="image.png"))
    else:
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