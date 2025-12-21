

async def send_code_block_with_return(channel, code_block: str, max_length: int = 2000):
    """
    Sends a code block, splitting into multiple code blocks if needed but never breaking a line of code.
    Returns the last message sent.
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
    if len(current_code) > len(code_prefix):
        current_code += code_suffix
        await channel.send(current_code)
