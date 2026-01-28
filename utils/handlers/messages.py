import re

import discord

from utils.handlers.codeblock import send_code_block, send_code_block_with_return
from utils.handlers.latex import LATEX_TO_EMOJI, convert_latex_to_png, detect_latex
from utils.handlers.table import detect_and_convert_tables
from utils.views.message import MessageView


async def smart_long_messages_with_view(
    channel,
    response,
    original_question,
    model,
    response_data,
    bot,
    max_length: int = 2000,
):
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
            result = await send_text_with_latex_with_return(channel, part, max_length)
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
            await send_text_with_latex(channel, part, max_length)


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


async def send_text_with_latex(channel, text: str, max_length: int = 2000):
    """
    Sends text, converting LaTeX expressions to images or replacing with emojis.
    """
    matches = detect_latex(text)
    if not matches:
        await send_text_in_chunks(channel, text, max_length)
        return

    current_text = ""
    last_end = 0
    for match in matches:
        start = text.find(match, last_end)
        if start == -1:
            continue
        # Add text before
        before = text[last_end:start]
        current_text += before
        # Process LaTeX
        latex = match.strip()
        if latex.startswith("```") and latex.endswith("```"):
            lines = latex.split("\n")
            if len(lines) >= 3 and lines[-1] == "```":
                latex = "\n".join(lines[1:-1])
        if latex.startswith("$") and latex.endswith("$"):
            latex = latex[1:-1]
        if latex.startswith(r"\[") and latex.endswith(r"\]"):
            latex = latex[2:-2]

        if latex in LATEX_TO_EMOJI:
            current_text += LATEX_TO_EMOJI[latex]
        else:
            # Send current text
            if current_text:
                await send_text_in_chunks(channel, current_text, max_length)
                current_text = ""
            # Send LaTeX image
            await send_latex_image(channel, match)
        last_end = start + len(match)
    # Add remaining text
    remaining = text[last_end:]
    current_text += remaining
    if current_text:
        await send_text_in_chunks(channel, current_text, max_length)


async def send_text_with_latex_with_return(channel, text: str, max_length: int = 2000):
    """
    Sends text, converting LaTeX expressions to images or replacing with emojis.
    Returns the last message sent.
    """
    matches = detect_latex(text)
    if not matches:
        return await send_text_in_chunks_with_return(channel, text, max_length)

    current_text = ""
    last_end = 0
    last_message = None
    for match in matches:
        start = text.find(match, last_end)
        if start == -1:
            continue
        # Add text before
        before = text[last_end:start]
        current_text += before
        # Process LaTeX
        latex = match.strip()
        if latex.startswith("```") and latex.endswith("```"):
            lines = latex.split("\n")
            if len(lines) >= 3 and lines[-1] == "```":
                latex = "\n".join(lines[1:-1])
        if latex.startswith("$") and latex.endswith("$"):
            latex = latex[1:-1]
        if latex.startswith(r"\[") and latex.endswith(r"\]"):
            latex = latex[2:-2]

        if latex in LATEX_TO_EMOJI:
            current_text += LATEX_TO_EMOJI[latex]
        else:
            # Send current text
            if current_text:
                result = await send_text_in_chunks_with_return(
                    channel, current_text, max_length
                )
                if result:
                    last_message = result
                current_text = ""
            # Send LaTeX image
            result = await send_latex_image_with_return(channel, match)
            if result:
                last_message = result
        last_end = start + len(match)
    # Add remaining text
    remaining = text[last_end:]
    current_text += remaining
    if current_text:
        result = await send_text_in_chunks_with_return(
            channel, current_text, max_length
        )
        if result:
            last_message = result
    return last_message


async def send_latex_image(channel, latex_match: str):
    """
    Sends a LaTeX formula as an image.
    """
    # Extract the LaTeX formula from the match
    latex = latex_match.strip()
    if latex.startswith("```") and latex.endswith("```"):
        lines = latex.split("\n")
        if len(lines) >= 3 and lines[-1] == "```":
            latex = "\n".join(lines[1:-1])
    if latex.startswith("$") and latex.endswith("$"):
        latex = latex[1:-1]
    if latex.startswith(r"\[") and latex.endswith(r"\]"):
        latex = latex[2:-2]

    result, success = convert_latex_to_png(latex)
    if success:
        if isinstance(result, str):
            # Complex LaTeX that couldn't be rendered, send as code block
            await channel.send(result)
        else:
            file = discord.File(result, filename="formula.png")
            await channel.send(file=file)
    else:
        await channel.send(f"Failed to render LaTeX: {latex}")


async def send_latex_image_with_return(channel, latex_match: str):
    """
    Sends a LaTeX formula as an image and returns the message.
    """
    # Extract the LaTeX formula from the match
    latex = latex_match.strip()
    if latex.startswith("```") and latex.endswith("```"):
        lines = latex.split("\n")
        if len(lines) >= 3 and lines[-1] == "```":
            latex = "\n".join(lines[1:-1])
    if latex.startswith("$") and latex.endswith("$"):
        latex = latex[1:-1]
    if latex.startswith(r"\[") and latex.endswith(r"\]"):
        latex = latex[2:-2]

    result, success = convert_latex_to_png(latex)
    if success:
        if isinstance(result, str):
            # Complex LaTeX that couldn't be rendered, send as code block
            message = await channel.send(result)
            return message
        else:
            file = discord.File(result, filename="formula.png")
            message = await channel.send(file=file)
            return message
    else:
        message = await channel.send(f"Failed to render LaTeX: {latex}")
        return message
