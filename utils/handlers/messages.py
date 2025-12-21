import re

from utils.handlers.codeblock import (send_code_block,
                                      send_code_block_with_return)
from utils.handlers.table import detect_and_convert_tables
from utils.views.message import MessageView


async def smart_long_messages_with_view(channel, response, original_question, model, response_data, bot, max_length: int = 2000):
    """
    Sends a long message to Discord with MessageView buttons, preserving code blocks and never splitting inside a code block.
    """    
    response = detect_and_convert_tables(response)
    pattern = re.compile(r"(```[\s\S]*?```)")
    parts = pattern.split(response)
    last_message = None
    
    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            result = await send_code_block_with_return(channel, part, max_length)
            if result:
                last_message = result
        else:
            result = await send_text_in_chunks_with_return(channel, part, max_length)
            if result:
                last_message = result
    
    # Ajouter la vue au dernier message envoyé
    if last_message:
        view = MessageView(original_question, model, response_data, bot)
        await last_message.edit(view=view)
        view.message = last_message


async def smart_long_messages(channel, response, max_length: int = 2000):
    """
    Sends a long message to Discord, preserving code blocks and never splitting inside a code block.
    """
    response = detect_and_convert_tables(response)
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


async def send_text_in_chunks_with_return(channel, text: str, max_length: int = 2000):
    """
    Sends plain text in chunks, never breaking lines in the middle if possible.
    Returns the last message sent.
    """
    if not text.strip():
        return None
        
    lines = text.splitlines(keepends=True)
    current_message = ""
    last_message = None
    
    for line in lines:
        if len(current_message) + len(line) > max_length:
            if current_message:
                last_message = await channel.send(current_message.rstrip())
            current_message = ""
        current_message += line
    
    if current_message.strip():
        last_message = await channel.send(current_message.rstrip())
    
    return last_message
