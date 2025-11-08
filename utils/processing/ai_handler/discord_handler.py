"""Discord message processing and Command parsing module."""

import logging
import re
from typing import Dict, Any

import discord

from utils.config.app_config import LOGGER_NAME
from utils.processing.ai_handler.core import generate_response
from utils.processing.table import detect_and_convert_tables
from utils.media.speech import send_voice_message

logger = logging.getLogger(LOGGER_NAME)

# Available AI models for Command parsing
AVAILABLE_MODELS = [
    "mistral", "openai", "claude", "llama", "deepseek",
    "qwen", "gemini", "grok", "perplexity", "cohere",
    "evilgpt", "glm", "kimi", "phi"
]


async def process_ai_response(bot: discord.Client, query: str, message: discord.Message):
    """Process AI response with Command parsing and message formatting."""
    try:
        parameters = {
            "history": True,
            "preprompt": True,
            "tools": False,
            "internet": False,
            "audio": False,
            "raw": False,
            "model": bot.user.id if isinstance(bot, discord.Client) else bot.id
        }

        # Parse Command flags from query
        while True:
            command_found = False
            
            model_match = re.search(r' -m \{([^}]+)\}$', query)
            if model_match:
                model_name = model_match.group(1)
                if model_name.lower() in AVAILABLE_MODELS:
                    parameters["model"] = model_name
                    query = query[:model_match.start()].rstrip()
                    logger.info(f"Model specified: {model_name}")
                    command_found = True
            
            elif query.endswith(" -h"):
                query = query[:-3].rstrip()
                parameters["history"] = False
                logger.info("History disabled")
                command_found = True
            elif query.endswith(" -p"):
                query = query[:-3].rstrip()
                parameters["preprompt"] = False
                logger.info("Preprompt disabled")
                command_found = True
            elif query.endswith(" -t"):
                query = query[:-3].rstrip()
                parameters["tools"] = False
                logger.info("Tools disabled")
                command_found = True
            elif query.endswith(" +i"):
                query = query[:-3].rstrip()
                parameters["internet"] = True
                logger.info("Internet enabled")
                command_found = True
            elif query.endswith(" +a"):
                query = query[:-3].rstrip()
                parameters["audio"] = True
                logger.info("Audio enabled")
                command_found = True
            elif query.endswith(" +r"):
                query = query[:-3].rstrip()
                parameters["raw"] = True
                logger.info("Raw mode enabled")
                command_found = True
            
            if not command_found:
                break

        logger.info(f"Query: {query}")
        if not query or query.isspace():
            logger.info(f"Empty message from {message.author.id}")
            query = "Hi! Please ask me a question."

        # Generate response
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
            logger.debug(f"Response generated successfully")
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            await message.channel.send("An error occurred while generating response.")
            return

        # Extract response text
        if isinstance(response, dict) and 'response' in response:
            response_text = response['response']
        elif isinstance(response, str):
            response_text = response
        else:
            logger.error(f"Unexpected response type: {type(response)}")
            await message.channel.send("An error occurred while processing response.")
            return
                
        # Send response
        try:
            if isinstance(response_text, bytes):
                await message.channel.send(
                    file=discord.File(__import__('io').BytesIO(response_text), filename="image.png")
                )
            elif isinstance(response_text, str):
                # Import locally to avoid circular dependency
                from utils.processing.message import smart_long_messages_with_view
                
                response_text = detect_and_convert_tables(response_text)
                await smart_long_messages_with_view(
                    message.channel, response_text, query,
                    parameters.get("model", "unknown"), response, bot
                )
                logger.debug(f"Response sent successfully")
            else:
                logger.error(f"Unexpected response text type: {type(response_text)}")
                await message.channel.send("An error occurred while sending response.")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            await message.channel.send("An error occurred while sending message.")

        # Generate audio if enabled
        try:
            if parameters.get("audio", False):
                await send_voice_message(message.channel, response_text)
                logger.debug(f"Voice message sent")
        except Exception as e:
            logger.error(f"Error generating voice: {str(e)}")
            await message.channel.send("An error occurred while generating voice.")

    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        await message.channel.send("An unexpected error occurred.")
