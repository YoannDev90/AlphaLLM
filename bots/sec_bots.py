import asyncio
import logging

import discord
from discord.ext import commands

from bots.bot import bot as main_bot
from config import ADDONS_BOTS_TOKENS, DEV_IDS, LOGGER_NAME
from utils.database.perms_conf import get_blacklist
from utils.handlers.messages import smart_long_messages_with_view
from utils.unified_text import Origin, Text_Model, unified_text_gen

intents = discord.Intents.default()
intents.message_content = True
logger = logging.getLogger(LOGGER_NAME)

def create_addon_bot():
    bot = commands.Bot(command_prefix="!", owner_ids=DEV_IDS, intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"Addon bot logged in as {bot.user} (ID: {bot.user.id})")
        await bot.change_presence(status=discord.Status.offline)

    @bot.event
    async def on_message(message):
        if message.author == bot.user or message.author == main_bot.user:
            return
        if message.author.id in await get_blacklist():
            await main_bot.get_channel(message.channel.id).send("❌ You are blacklisted from using this bot.")
            return

        files = []
        if message.attachments:
            for attachment in message.attachments:
                files.append(attachment.url)

        logger.debug(
            f"Addon bot processing message for user {message.author.id}, input: {message.content}"
        )
        try:
            response = [
                result
                async for result in unified_text_gen(
                    user_id=message.author.id,
                    conv_id=message.channel.id,
                    input=message.content,
                    model=Text_Model.AUTO,
                    files=files if files else None,
                    origin=Origin.DISCORD,
                    message=message,
                    bot=bot,
                    stream=False,
                    use_memory=True,
                )
            ]
            logger.debug(f"unified_text_gen returned {len(response)} results")
            result = response[0] if response else None
            if result:
                logger.debug(
                    f"Result model: {result.model}, response length: {len(result.response)}"
                )
                async with main_bot.get_channel(message.channel.id).typing():
                    if result.response.startswith("generated_image"):
                        import base64
                        import io

                        parts = result.response.split(":", 1)
                        if len(parts) == 2:
                            base64_data = parts[1]
                            try:
                                image_bytes = base64.b64decode(base64_data)
                                image_file = discord.File(
                                    io.BytesIO(image_bytes), filename="generated_image.png"
                                )
                                await main_bot.get_channel(message.channel.id).send(file=image_file)
                            except Exception as e:
                                logger.error(f"Erreur lors de l'envoi de l'image: {e}")
                                await smart_long_messages_with_view(
                                    message.channel,
                                    result.response,
                                    message.content,
                                    result.model,
                                    result,
                                    main_bot,
                                )
                    else:
                        logger.debug("About to call smart_long_messages_with_view")
                        try:
                            await smart_long_messages_with_view(
                                message.channel,
                                result.response,
                                message.content,
                                result.model,
                                result,
                                main_bot,
                            )
                            logger.debug(
                                "smart_long_messages_with_view completed successfully"
                            )
                        except Exception as e:
                            logger.error(f"Error sending response: {e}")
                            await main_bot.get_channel(message.channel.id).send(
                                "Sorry, an error occurred while sending the response."
                            )
            else:
                logger.debug("No result from unified_text_gen")
                await main_bot.get_channel(message.channel.id).send(
                    "Sorry, an error occurred while processing your request."
                )
        except Exception as e:
            logger.error(f"Error in addon bot on_message: {e}")

    return bot


async def run_addon_bots():
    if not ADDONS_BOTS_TOKENS:
        logger.info("No addon bot tokens configured")
        return

    bots = [create_addon_bot() for _ in ADDONS_BOTS_TOKENS]
    
    tasks = []
    for bot, token in zip(bots, ADDONS_BOTS_TOKENS):
        task = asyncio.create_task(run_single_addon_bot(bot, token))
        tasks.append(task)
    
    await asyncio.gather(*tasks, return_exceptions=True)


async def run_single_addon_bot(bot, token):
    try:
        await bot.start(token)
    except Exception as exc:
        logger.error(f"Addon bot failed: {type(exc).__name__}: {exc}")
    finally:
        if not bot.is_closed():
            await bot.close()
        logger.info("Addon bot stopped")
