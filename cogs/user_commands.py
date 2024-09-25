import discord
from discord import app_commands
from discord.ext import commands

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Affiche la liste des commandes")
    async def help_command(self, interaction: discord.Interaction):
        help_text = """
        **Commandes disponibles :**
        /help - Affiche cette liste de commandes
        /info - Fournit des informations sur le bot
        /ping - Vérifie la latence du bot
        """
        await interaction.response.send_message(help_text)

    @app_commands.command(name="info", description="Fournit des informations sur le bot")
    async def info_command(self, interaction: discord.Interaction):
        info_text = """
        **Informations sur le bot :**
        Nom : AlphaLLMBot
        Version : 2.0
        Créateur : Yoann Dumont @the_yerminator
        Description : Ce bot utilise l'API OpenRouter et le modèle Reflection 70B pour générer des réponses intelligentes.
        """
        await interaction.response.send_message(info_text)

    @app_commands.command(name="ping", description="Vérifie la latence du bot")
    async def ping_command(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! Latence : {latency}ms")
