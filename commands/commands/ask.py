import discord
from discord import app_commands
import logging
from utils.config import logger_name
from dotenv import load_dotenv
from utils.ai_process import process_ai_response
from utils.msg_process import ask_cmd_process
import os

load_dotenv()
logger = logging.getLogger(logger_name)

MODELS = [
        app_commands.Choice(name="Llama 3.3 70b", value="cerebras/llama3.3-70b"),
        app_commands.Choice(name="GPT-5", value="openai/gpt-5"),
        app_commands.Choice(name="Mistral Medium", value="mistral/mistral-medium-latest"),
        app_commands.Choice(name="Qwen 3 32b", value="cerebras/qwen-3-32b"),
        app_commands.Choice(name="Gemini 2.5 Flash", value="openai/gemini-2.5-flash"),
        app_commands.Choice(name="Perplexity", value="openai/sonar"),
        app_commands.Choice(name="EvilGPT", value="openai/evil"),
        app_commands.Choice(name="Grok 4", value="openai/grok-4"),
        app_commands.Choice(name="Claude 3 5 Haiku", value="openai/claude-3-5-haiku-20241022"),
        app_commands.Choice(name="Kimi K2 Instruct", value="openai/kimi-k2-instruct"),
        app_commands.Choice(name="Deepseek", value="openai/deepseek-v3.1"),
        app_commands.Choice(name="GLM 4.5", value="openai/glm-4.5"),
        app_commands.Choice(name="Phi 4", value="openai/phi-4"),
        app_commands.Choice(name="Command R", value="cohere/command-r")
    ]

async def setup(bot: discord.Client):
    @bot.tree.command(name="ask", description="Ask something")
    @app_commands.describe(input="Ask something")
    @app_commands.choices(model=MODELS)
    async def ask(interaction: discord.Interaction, input: str, model: str = "cerebras/llama3.3-70b", search_internet: bool = None):
        logger.info(f"Commande /ask exécutée par {interaction.user.display_name}")
        try:
            await ask_cmd_process(bot, input, model, search_internet, interaction)
        except Exception as e:
            logger.error(f"Error in ask command: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred while processing your request.", ephemeral=True)
            else:
                await interaction.followup.send("An error occurred while processing your request.", ephemeral=True)
