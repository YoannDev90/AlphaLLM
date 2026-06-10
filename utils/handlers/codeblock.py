"""Helpers for sending Discord code blocks."""

import discord


async def send_code_block_with_return(
    channel, code_block: str, max_length: int = 2000, bot=None
):
    """Send a code block, splitting it when it exceeds Discord limits.

    Parameters
    ----------
    channel : Any
        Discord channel-like target.
    code_block : str
        Code block text to send.
    max_length : int
        Maximum message length. Default is 2000.
    bot : Any
        Optional bot instance used for channel resolution. Default is None.

    Returns
    -------
    discord.Message | None
        Last message sent, or None.
    """
    first_line_end = code_block.find("\n")
    if first_line_end == -1:
        language = ""
        code = code_block[3:-3]
    else:
        language = code_block[3:first_line_end].strip()
        code = code_block[first_line_end + 1 : -3]

    if language.lower() in ["latex", "tex"]:
        from utils.handlers.messages import MessageSender

        return await MessageSender(channel, bot).send_latex_image(code_block)

    code_lines = code.splitlines(keepends=True)
    code_prefix = f"```{language}\n" if language else "```"
    code_suffix = "```"
    current_code = code_prefix
    last_message = None

    for line in code_lines:
        if len(current_code) + len(line) + len(code_suffix) > max_length:
            current_code += code_suffix
            last_message = await channel.send(current_code)
            current_code = code_prefix
        current_code += line

    if len(current_code) > len(code_prefix):
        current_code += code_suffix
        last_message = await channel.send(current_code)
    return last_message


async def send_code_block(channel, code_block: str, max_length: int = 2000, bot=None):
    """Send a code block without returning the resulting message.

    Parameters
    ----------
    channel : Any
        Discord channel-like target.
    code_block : str
        Code block text to send.
    max_length : int
        Maximum message length. Default is 2000.
    bot : Any
        Optional bot instance used for channel resolution. Default is None.

    Returns
    -------
    None
        No value returned.
    """
    await send_code_block_with_return(channel, code_block, max_length, bot)
