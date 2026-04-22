# import logging

# import discord
# from discord import app_commands

# from config import LOGGER_NAME
# from utils.discord_utils.permission_checker import PermissionChecker
# from utils.handlers.messages import smart_long_messages
# from utils.unified_text import Origin, unified_text_gen

# logger = logging.getLogger(LOGGER_NAME)
# perms_checker = PermissionChecker()

# logger = logging.getLogger(LOGGER_NAME)

# MODELS = [
#     app_commands.Choice(name="Llama", value="llama"),
#     app_commands.Choice(name="GPT", value="openai"),
#     app_commands.Choice(name="Mistral", value="mistral"),
#     app_commands.Choice(name="Qwen", value="qwen"),
#     app_commands.Choice(name="Gemini", value="gemini"),
#     app_commands.Choice(name="Sonar", value="sonar"),
#     app_commands.Choice(name="Grok", value="grok"),
#     app_commands.Choice(name="Claude", value="claude"),
#     app_commands.Choice(name="DeepSeek", value="deepseek"),
#     app_commands.Choice(name="GLM", value="glm"),
# ]


# async def setup(bot: discord.Client):
#     @bot.tree.command(name="ask", description="Ask something")
#     @app_commands.describe(input="Ask something")
#     @app_commands.choices(model=MODELS)
#     async def ask(
#         interaction: discord.Interaction,
#         input: str,
#         model: str = "auto",
#         attachment: discord.Attachment = None,
#     ):
#         logger.info(f"Command /ask executed by {interaction.user.display_name}")

#         # Check permissions
#         authorized, reason = await perms_checker.is_authorized_int(interaction)
#         if not authorized:
#             await interaction.response.send_message(f"Error: {reason}", ephemeral=True)
#             return

#         await interaction.response.defer()
#         try:
#             results = [
#                 result
#                 async for result in unified_text_gen(
#                     user_id=interaction.user.id,
#                     conv_id=interaction.channel.id,
#                     input=input,
#                     model=model,
#                     files=[attachment] if attachment else None,
#                     origin=Origin.DISCORD,
#                     message=interaction,
#                     bot=bot,
#                     stream=False,
#                 )
#             ]
#             result = results[0] if results else None
#             if result:
#                 await smart_long_messages(interaction.channel, result.response)
#             else:
#                 await interaction.followup.send(
#                     "Sorry, an error occurred while processing your request."
#                 )
#         except Exception as e:
#             logger.error(f"Error in ask command: {e}")
#             await interaction.followup.send(
#                 "An error occurred while processing your request.", ephemeral=True
#             )
