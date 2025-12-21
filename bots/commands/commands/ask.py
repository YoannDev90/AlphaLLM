import logging

import discord
from discord import app_commands

from config import LOGGER_NAME
from utils.handlers.messages import smart_long_messages
from utils.unified_text import Origin, unified_text_manager

logger = logging.getLogger(LOGGER_NAME)

MODELS = [
        app_commands.Choice(name="Llama", value="llama"),
        app_commands.Choice(name="GPT", value="openai"),
        app_commands.Choice(name="Mistral", value="mistral"),
        app_commands.Choice(name="Qwen", value="qwen"),
        app_commands.Choice(name="Gemini", value="gemini"),
        app_commands.Choice(name="Sonar", value="sonar"),
        app_commands.Choice(name="Evil", value="evil"),
        app_commands.Choice(name="Grok", value="grok"),
        app_commands.Choice(name="Claude", value="claude"),
        app_commands.Choice(name="Kimi", value="kimi"),
        app_commands.Choice(name="DeepSeek", value="deepseek"),
        app_commands.Choice(name="GLM", value="glm"),
        app_commands.Choice(name="Phi", value="phi"),
        app_commands.Choice(name="Cohere", value="cohere"),
        app_commands.Choice(name="Granite", value="granite"),
        app_commands.Choice(name="Hermes", value="hermes"),
        app_commands.Choice(name="Hunyuan", value="hunyuan"),
        app_commands.Choice(name="Jamba", value="jamba"),
        app_commands.Choice(name="Longcat", value="longcat"),
        app_commands.Choice(name="Mercury", value="mercury"),
        app_commands.Choice(name="Minimax", value="minimax"),
        app_commands.Choice(name="Nemotron", value="nemotron"),
        app_commands.Choice(name="Rocinante", value="rocinante"),
        app_commands.Choice(name="Seed", value="seed"),
        app_commands.Choice(name="Yi", value="yi")
    ]

async def setup(bot: discord.Client):
    @bot.tree.command(name="ask", description="Ask something")
    @app_commands.describe(input="Ask something")
    @app_commands.choices(model=MODELS)
    async def ask(interaction: discord.Interaction, input: str, model: str = "auto"):
        logger.info(f"Commande /ask exécutée par {interaction.user.display_name}")
        await interaction.response.defer()
        try:  
            results = [result async for result in unified_text_manager(
                user_id=interaction.user.id,
                conv_id=interaction.channel.id,
                input=input,
                model=model,
                files=None,
                origin=Origin.DISCORD,
                message=interaction,
                bot=bot,
                stream=False
            )]
            result = results[0]
            await smart_long_messages(interaction.channel, result.response)
        except Exception as e:
            logger.error(f"Error in ask command: {e}")
            await interaction.followup.send("An error occurred while processing your request.", ephemeral=True)
