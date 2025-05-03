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
from markdown_analysis import MarkdownAnalysis
from table2ascii import table2ascii, PresetStyle
import importlib
import os
from pathlib import Path
from io import BytesIO
import discord
import random
import re
import importlib
from typing import List

logger = logging.getLogger('AlphaLLM')
URL_REGEX = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+\/?(?:\S*)'

async def process_ai_response(message):
    logger.info(f"Bot mentionné par {message.author.display_name} ({message.author.id})")
    new_query(message.author.id)
    new_interaction(message.author.id)
    mentioned_roles = [role for role in message.role_mentions if role in message.guild.me.roles]
    selected_role = mentioned_roles[0] if mentioned_roles else None
    model_name = "cerebras"
    model_name = get_def_model(message.author.id) if get_def_model(message.author.id) else model_name
    # if selected_role:
    #     model_name = get_model_from_role(message.guild.id, selected_role.id)
    #     if not model_name:
    #         await message.channel.send(
    #             f"Le rôle `{selected_role.name}` n'a pas de modèle associé. "
    #             f"Veuillez utiliser la commande `/models` pour configurer un modèle."
    #         )
    #         return

    query = message.content.replace(f"<@{message.guild.me.id}>", "").strip()
    logger.info(f"Message reçu : {query}")
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
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse : {e}")
        await message.channel.send("Une erreur s'est produite lors de la génération de la réponse.")
        return

    # images = []
    # docs = []
    # links = re.findall(URL_REGEX, message.content)
    # for attachment in message.attachments:
    #     if attachment.content_type and attachment.content_type.startswith("image"):
    #         images.append(attachment.url)
    #     else:
    #         docs.append(attachment.url)

    # if docs:
    #     for doc_url in docs:
    #         doc_content = await md_conversion(doc_url)
    #         query += f"\nContenu du document :\n{doc_content}"

    # if links:
    #     for link in links:
    #         query += f"\n\nLien : {link}"
    #         link_content = await get_text_from_url(link)
    #         if link_content is not None:
    #             query += f"\nContenu :\n{link_content}"
    #         else:
    #             query += f"\nLe lien `{link}` n'est pas accessible ou ne contient pas de texte."


    # try:
    #     module_name = model_name.replace("-", "_")
    #     module_path = f"models.{module_name}"
    #     model_module = importlib.import_module(module_path)

    #     if not hasattr(model_module, module_name):
    #         logger.error(f"Le modèle `{model_name}` n'est pas implémenté.")
    #         await message.channel.send(f"Le modèle `{model_name}` n'est pas implémenté.")
    #         return

    #     response_function = getattr(model_module, module_name)
    #     response = await response_function(query)
    
    # except Exception as e:
    #     logger.error(f"Erreur lors du traitement avec le modèle {model_name} : {e}")
    #     await message.channel.send(f"Une erreur s'est produite avec le modèle `{model_name}`.")

    try:
        await smart_long_messages(message.channel, response)
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message : {e}")
        await message.channel.send("Une erreur s'est produite lors de l'envoi du message.")

    try:
        if get_audio_gen_active(message.author.id):
            await send_voice_message(message.channel, response, get_audio_voice(message.author.id))
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la voix : {e}")
        await message.channel.send("Une erreur s'est produite lors de la génération de la voix.")

# async def smart_long_messages(channel, text: str, max_length: int = 2000):
#     """
#     Sends a long message to Discord, preserving code blocks and never splitting inside a code block.
#     """
#     # Pattern to split on code blocks (captures the ```lang\n...```
#     pattern = re.compile(r"(```[\s\S]*?```)")
#     parts = pattern.split(text)
#     for part in parts:
#         if part.startswith("```") and part.endswith("```"):
#             await send_code_block(channel, part, max_length)
#         else:
#             await send_text_in_chunks(channel, part, max_length)

# async def send_text_in_chunks(channel, text: str, max_length: int = 2000):
#     """
#     Sends plain text in chunks, never breaking lines in the middle if possible.
#     """
#     lines = text.splitlines(keepends=True)
#     current_message = ""
#     for line in lines:
#         if len(current_message) + len(line) > max_length:
#             if current_message:
#                 await channel.send(current_message.rstrip())
#             current_message = ""
#         current_message += line
#     if current_message.strip():
#         await channel.send(current_message.rstrip())

# async def send_code_block(channel, code_block: str, max_length: int = 2000):
#     """
#     Sends a code block, splitting into multiple code blocks if needed but never breaking a line of code.
#     """
#     # Extract the language (if any)
#     first_line_end = code_block.find('\n')
#     if first_line_end == -1:
#         language = ""
#         code = code_block[3:-3]
#     else:
#         language = code_block[3:first_line_end].strip()
#         code = code_block[first_line_end+1:-3]

#     code_lines = code.splitlines(keepends=True)
#     code_prefix = f"```{language}\n" if language else "```"
#     code_suffix = "```"
#     current_code = code_prefix
#     for line in code_lines:
#         # +3 for closing ```
#         if len(current_code) + len(line) + len(code_suffix) > max_length:
#             current_code += code_suffix
#             await channel.send(current_code)
#             current_code = code_prefix
#         current_code += line
#     if current_code.strip() != code_prefix.strip():
#         current_code += code_suffix
#         await channel.send(current_code)






















async def smart_long_messages(channel, text: str, max_length: int = 2000):
    """
    Envoie un long message sur Discord, en préservant les blocs de code et les tableaux markdown convertis en ascii,
    chaque bloc (code ou tableau) étant envoyé dans un message distinct.
    Utilise markdown-analysis pour parser le markdown.
    """
    md = MarkdownAnalysis(text)
    md.parse()

    # Récupérer tous les blocs de code et tableaux avec leurs positions
    code_blocks = md.get_code_blocks()  # dicts avec 'content', 'lang', 'start', 'end'
    tables = md.get_tables()            # dicts avec 'content', 'start', 'end'

    # Fusionner tous les blocs dans l'ordre d'apparition
    events = []
    for cb in code_blocks:
        events.append((cb['start'], 'code', cb))
    for tb in tables:
        events.append((tb['start'], 'table', tb))
    events.sort(key=lambda x: x[0])

    pos = 0
    for start, typ, block in events:
        # Envoyer le texte brut avant ce bloc
        if start > pos:
            await send_text_in_chunks(channel, text[pos:start], max_length)
        if typ == 'code':
            lang = block.get('lang', '')
            code_content = block['content']
            code_block = f"``````" if lang else f"``````"
            await send_code_block(channel, code_block, max_length)
        elif typ == 'table':
            md_table = block['content']
            ascii_table = markdown_table_to_ascii(md_table)
            ascii_block = f"``````"
            await send_code_block(channel, ascii_block, max_length)
        pos = block['end']

    # Envoyer le reste du texte après le dernier bloc
    if pos < len(text):
        await send_text_in_chunks(channel, text[pos:], max_length)

def markdown_table_to_ascii(md_table: str) -> str:
    # Utilise markdown-analysis pour parser le tableau markdown en ASCII
    lines = [line.strip() for line in md_table.strip().split('\n') if line.strip()]
    header = [h.strip() for h in lines[0].split('|') if h.strip()]
    body = []
    for line in lines[2:]:
        row = [cell.strip() for cell in line.split('|') if cell.strip()]
        body.append(row)
    ascii_table = table2ascii(header=header, body=body, style=PresetStyle.ascii_box)
    return ascii_table

async def send_text_in_chunks(channel, text: str, max_length: int = 2000):
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
    first_line_end = code_block.find('\n')
    if first_line_end == -1:
        language = ""
        code = code_block[3:-3]
    else:
        language = code_block[3:first_line_end].strip()
        code = code_block[first_line_end+1:-3]

    code_lines = code.splitlines(keepends=True)
    code_prefix = f"``````\n"
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