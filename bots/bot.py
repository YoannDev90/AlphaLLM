import asyncio
import logging

import discord
from discord.ext import commands

from bots.commands.cmds import setup_commands
from config import BOT_TOKEN, DEBUG, DEV_IDS, LOGGER_NAME
from utils.discord_utils.commands_ids import command_id_manager
from utils.discord_utils.permission_checker import PermissionChecker
from utils.handlers.messages import smart_long_messages_with_view
from utils.unified_text import Origin, Text_Model, unified_text_gen

perms_checker = PermissionChecker()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", owner_ids=DEV_IDS, intents=intents)
logger = logging.getLogger(LOGGER_NAME)


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    activity = discord.CustomActivity(name="🤖 Try @AlphaLLM or /commands")
    await bot.change_presence(activity=activity, status=discord.Status.idle)
    await bot.tree.sync()
    command_id_manager.set_bot(bot)
    asyncio.create_task(command_id_manager.fetch_command_ids())
    logger.info("Fetch des IDs de commandes lancé en arrière-plan")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    authorized, reason = await perms_checker.is_authorized_msg(message)
    if not authorized:
        if reason not in ["Bot non mentionné", "Mention @everyone, @here ou rôle"]:
            await message.channel.send(f"Erreur : {reason}")
        return

    files = []
    if message.attachments:
        for attachment in message.attachments:
            files.append(attachment.url)

    logger.debug(
        f"About to call unified_text_gen for user {message.author.id}, input: {message.content}"
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
            async with message.channel.typing():
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
                            await message.channel.send(file=image_file)
                        except Exception as e:
                            logger.error(f"Erreur lors de l'envoi de l'image: {e}")
                            await smart_long_messages_with_view(
                                message.channel,
                                result.response,
                                message.content,
                                result.model,
                                result,
                                bot,
                            )
                    else:
                        await smart_long_messages_with_view(
                            message.channel,
                            result.response,
                            message.content,
                            result.model,
                            result,
                            bot,
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
                            bot,
                        )
                        logger.debug(
                            "smart_long_messages_with_view completed successfully"
                        )
                    except Exception as e:
                        logger.error(f"Error sending response: {e}")
                        await message.channel.send(
                            "Sorry, an error occurred while sending the response."
                        )
        else:
            logger.debug("No result from unified_text_gen")
            await message.channel.send(
                "Sorry, an error occurred while processing your request."
            )
    except Exception as e:
        logger.error(f"Error in on_message: {e}")


@bot.event
async def on_guild_join(guild):
    logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")


@bot.event
async def on_guild_remove(guild):
    logger.info(f"Removed from guild: {guild.name} (ID: {guild.id})")


async def run_bot():
    mode_label = "BetaLLM" if DEBUG else "AlphaLLM"
    await setup_commands(bot, is_admin_bot=False)
    logger.info(f"Starting {mode_label}")
    try:
        logger.info("Logging in...")
        await bot.start(BOT_TOKEN)
    except Exception as exc:
        logger.error(f"Bot failed: {type(exc).__name__}: {exc}")
    finally:
        if not bot.is_closed():
            await bot.close()
        logger.info("Bot stopped")
