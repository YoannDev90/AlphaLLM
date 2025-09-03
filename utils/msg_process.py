import discord
import logging
from utils.config import logger_name
from utils.database import get_blacklist, get_allowed_channels, get_allowed_roles
from utils.ai_process import process_ai_response
from utils.user_manager import new_interaction, new_query
from utils.table_converter import detect_and_convert_tables

logger = logging.getLogger(logger_name)

def is_bot_mentioned(bot, message):
    if not message.guild:
        return bot.user.mentioned_in(message)
    else:
        if message.mention_everyone:
            return False
        if bot.user.mentioned_in(message):
            return True
        if message.guild.me and any(role in message.role_mentions for role in message.guild.me.roles):
            return True
        return False

async def is_blacklist(message):
    blacklist_data = await get_blacklist()

    blacklist_entry = next((entry for entry in blacklist_data if entry.get('id_discord') == message.author.id), None)
    if blacklist_entry:
        reason = blacklist_entry.get('reason', 'Unspecified')
        logger.info(f"Message de {message.author.display_name} (ID: {message.author.id}) ignoré - Liste noire")
        await message.channel.send(f"⛔️ You are blacklisted from the bot (<@{message.author.id}>) - Reason: **{reason}**")
        return
    
async def is_channel_allowed(message):
    forbidden_channels = await get_allowed_channels(message.guild.id)
    if message.channel.id in forbidden_channels:
        logger.info(f"Message de {message.author.display_name} (ID: {message.author.id}) ignoré - Canal non autorisé")
        await message.channel.send(f"⛔️ You are not allowed to use this bot in this channel (<#{message.channel.id}>)")
        return
    return

async def is_role_allowed(message):
    forbidden_roles = await get_allowed_roles(message.guild.id)
    user = message.author
    user_role_ids = [role.id for role in user.roles]
    
    if any(role_id in forbidden_roles for role_id in user_role_ids):
        logger.info(f"Message de {message.author.display_name} (ID: {message.author.id}) ignoré - Rôle non autorisé")
        await message.channel.send(f"⛔️ You are not allowed to use this bot with your current role(s)")
        return
    return

async def message_process(bot, message):
    if message.author.bot:
        return
    
    if not message.author.bot:
        logger.debug(f"Message reçu de {message.author}: {message.content}")
        bot_mentioned = is_bot_mentioned(bot, message)

        if bot_mentioned:
            await is_blacklist(message)
            await is_channel_allowed(message)
            await is_role_allowed(message)

            logger.info(f"Bot mentionné par {message.author.display_name} ({message.author.id})")
            new_query(message.author.id)
            new_interaction(message.author.id)

            bot_mention = f"<@{bot.user.id}>"
            query = message.content.replace(bot_mention, "").strip()

            async with message.channel.typing():
                await process_ai_response(bot, query, message)

async def ask_cmd_process(bot, query, model, internet, interaction):
    new_query(interaction.user.id)
    new_interaction(interaction.user.id)

    messages = [
        {"role": "user", "content": query}
    ]

    parameters = {"internet": internet if internet is not None else False, "raw": False}

    try:
        await interaction.response.defer()
        
        match model:
            case "cerebras/llama3.3-70b":
                from models.llama import llama_chat
                resp = await llama_chat(messages, parameters)
            case "openai/gpt-5":
                from models.openai import openai_chat
                resp = await openai_chat(messages, parameters)
            case "mistral/mistral-medium-latest":
                from models.mistral import mistral_chat
                resp = await mistral_chat(messages, parameters)
            case "openai/deepseek-v3.1":
                from models.deepseek import deepseek_chat
                resp = await deepseek_chat(messages, parameters)
            case "cerebras/qwen-3-32b":
                from models.qwen import qwen_chat
                resp = await qwen_chat(messages, parameters)
            case "openai/gemini-2.5-flash":
                from models.gemini import gemini_chat
                resp = await gemini_chat(messages, parameters)
            case "openai/sonar":
                from models.perplexity import perplexity_chat
                resp = await perplexity_chat(messages, parameters)
            case "openai/evil":
                from models.evilgpt import evilgpt_chat
                resp = await evilgpt_chat(messages, parameters)
            case "openai/grok-4":
                from models.grok import grok_chat
                resp = await grok_chat(messages, parameters)
            case "openai/phi-4":
                from models.phi import phi_chat
                resp = await phi_chat(messages, parameters)
            case "openai/claude-3-5-haiku-20241022":
                from models.claude import claude_chat
                resp = await claude_chat(messages, parameters)
            case "openai/kimi-k2-instruct":
                from models.kimi import kimi_chat
                resp = await kimi_chat(messages, parameters)
            case "openai/glm-4.5":
                from models.glm import glm_chat
                resp = await glm_chat(messages, parameters)
            case _:
                from models.llama import llama_chat
                resp = await llama_chat(messages, parameters)

        response_text = resp.get("response", "No response generated")
        response_text = detect_and_convert_tables(response_text)
        await smart_long_messages_interaction(interaction, response_text)
        
    except Exception as e:
        logger.error(f"Error in ask_cmd_process: {e}")
        error_msg = "An error occurred while processing your request."
        if interaction.response.is_done():
            await interaction.followup.send(error_msg)
        else:
            await interaction.response.send_message(error_msg)

async def smart_long_messages_interaction(interaction, response, max_length: int = 2000):
    """
    Sends a long message to Discord via interaction, preserving code blocks and never splitting inside a code block.
    """
    import re
    
    pattern = re.compile(r"(```[\s\S]*?```)")
    parts = pattern.split(response)
    first_message = True
    
    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            await send_code_block_interaction(interaction, part, max_length, first_message)
            first_message = False
        else:
            await send_text_in_chunks_interaction(interaction, part, max_length, first_message)
            if part.strip():
                first_message = False

async def send_text_in_chunks_interaction(interaction, text: str, max_length: int = 2000, first_message: bool = True):
    """
    Sends plain text in chunks via interaction, never breaking lines in the middle if possible.
    """
    if not text.strip():
        return
        
    lines = text.splitlines(keepends=True)
    current_message = ""
    
    for line in lines:
        if len(current_message) + len(line) > max_length:
            if current_message:
                if first_message:
                    await interaction.followup.send(current_message.rstrip())
                    first_message = False
                else:
                    await interaction.followup.send(current_message.rstrip())
            current_message = ""
        current_message += line
    
    if current_message.strip():
        if first_message:
            await interaction.followup.send(current_message.rstrip())
        else:
            await interaction.followup.send(current_message.rstrip())

async def send_code_block_interaction(interaction, code_block: str, max_length: int = 2000, first_message: bool = True):
    """
    Sends a code block via interaction, splitting into multiple code blocks if needed but never breaking a line of code.
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
            if first_message:
                await interaction.followup.send(current_code)
                first_message = False
            else:
                await interaction.followup.send(current_code)
            current_code = code_prefix
        current_code += line
    
    if current_code.strip() != code_prefix.strip():
        current_code += code_suffix
        if first_message:
            await interaction.followup.send(current_code)
        else:
            await interaction.followup.send(current_code)