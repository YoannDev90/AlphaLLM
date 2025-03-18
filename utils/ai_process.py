#ai_process.py

import logging
from models.cerebras import cerebras
from models.openai import openai
from models.openai_large import openai_large
from utils.md_converter import md_conversion
from utils.langs import get_translation
import re
from io import BytesIO
import discord
import random

logger = logging.getLogger('AlphaLLM')

async def process_ai_response(message, query):
    if message.attachments:
        images = []
        docs = []
        for attachment in message.attachments:
            if attachment.content_type.endswith(('png', 'jpeg', 'jpg', 'gif', 'webp', 'bmp', 'tiff', 'svg', 'pdf')):
                images.append(attachment.url)
            else:
                docs.append(attachment.url)
        if images != []:
            logger.info(f"Images trouvées dans le message")
        if docs:
            logger.info(f"Documents trouvés dans le message")
            for doc in docs:
                doc_to_md = await md_conversion(doc)
                query += "\nHere is the content of the document:\n"
                query += doc_to_md

    response = await cerebras(query)
    await smart_long_messages(message.channel, response)
    #response = await openai(query, images)
    #await smart_long_messages(message.channel, response)
    #response = await openai_large(query, images)
    #await smart_long_messages(message.channel, response)
        
    #await smart_long_messages(message.channel, response)

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
