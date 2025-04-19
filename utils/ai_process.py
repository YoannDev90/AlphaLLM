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
    model_name = get_def_model(message.author.id)
    # if selected_role:
    #     model_name = get_model_from_role(message.guild.id, selected_role.id)
    #     if not model_name:
    #         await message.channel.send(
    #             f"Le rôle `{selected_role.name}` n'a pas de modèle associé. "
    #             f"Veuillez utiliser la commande `/models` pour configurer un modèle."
    #         )
    #         return

    if selected_role:
        query = message.content.replace(f"<@&{selected_role.id}>", "").strip()
    else:
        query = message.content.replace(f"<@{message.guild.me.id}>", "").strip()

    try:
        response = await generate_response(
            user_id=int(message.author.id),
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


async def smart_long_messages(channel, text: str, max_length: int = 2000):
    if len(text) <= max_length:
        await channel.send(text)
        return

    code_block_regex = r"```?```"
    code_blocks = list(re.finditer(code_block_regex, text))
    last_cut = 0
    in_code_block = False
    current_code_block = ""

    for i, match in enumerate(code_blocks):
        start, end = match.span()

        if not in_code_block:
            if start > last_cut:
                text_to_send = text[last_cut:start].strip()
                if text_to_send:
                    await send_text_in_chunks(channel, text_to_send, max_length)

            in_code_block = True
            current_code_block = text[start:end]
            last_cut = end
        else:
            in_code_block = False
            current_code_block += text[last_cut:end]
            await channel.send(current_code_block)
            last_cut = end

    if in_code_block:
        current_code_block += text[last_cut:]
        await channel.send(current_code_block)
    elif last_cut < len(text):
        text_to_send = text[last_cut:].strip()
        if text_to_send:
            await send_text_in_chunks(channel, text_to_send, max_length)

async def send_text_in_chunks(channel, text: str, max_length: int):
    lines = text.splitlines()
    current_message = ""
    for line in lines:
        if len(current_message) + len(line) + 1 > max_length:
            if current_message:
                await channel.send(current_message)
            current_message = ""
        current_message += line + "\n"

    if current_message:
        await channel.send(current_message)
