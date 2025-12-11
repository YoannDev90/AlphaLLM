import discord
from discord import app_commands
from config import LOGGER_NAME
import logging

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
        app_commands.Choice(name="Kimi-K2", value="kimi"),
        app_commands.Choice(name="DeepSeek", value="deepseek"),
        app_commands.Choice(name="GLM", value="glm"),
        app_commands.Choice(name="Phi", value="phi"),
        app_commands.Choice(name="Cohere", value="cohere")
    ]

async def setup(bot: discord.Client):
    @bot.tree.command(name="ask", description="Ask something")
    @app_commands.describe(input="Ask something")
    @app_commands.choices(model=MODELS)
    async def ask(interaction: discord.Interaction, input: str, model: str = "llama"):
        logger.info(f"Commande /ask exécutée par {interaction.user.display_name}")
        try:
            pass
        except Exception as e:
            logger.error(f"Error in ask command: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred while processing your request.", ephemeral=True)
            else:
                await interaction.followup.send("An error occurred while processing your request.", ephemeral=True)
