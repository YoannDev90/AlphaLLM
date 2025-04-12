import discord
from discord import app_commands
from supabase import Client, create_client, ClientOptions
import os
import logging

logger = logging.getLogger('AlphaLLM')

# Configuration Supabase
supabase = Client(
    os.getenv("DB_URL"),
    os.getenv("DB_KEY"),
    options=ClientOptions(headers={"Authorization": f"Bearer {os.getenv('JWT_KEY')}"})
)

async def setup(bot: discord.Client):
    @bot.tree.command(name="langue", description="Définit votre langue")
    @app_commands.choices(langue=[
        app_commands.Choice(name="Français 🇫🇷", value="fr"),
        app_commands.Choice(name="English 🇬🇧", value="en"),
        app_commands.Choice(name="Español 🇪🇸", value="es"),
        app_commands.Choice(name="Deutsch 🇩🇪", value="de")
    ])
    async def langue(interaction: discord.Interaction, langue: app_commands.Choice[str]):
        try:
            # Mise à jour dans Supabase
            supabase.table("user_settings").upsert({
                "id_discord": interaction.user.id,
                "lang": langue
            }).execute()

            # Réponse avec embed
            embed = discord.Embed(
                title="🌍 Langue mise à jour",
                description=f"Votre langue a été définie sur : **{langue.upper()}**",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Langue mise à jour pour {interaction.user.display_name} : {langue}")

        except Exception as e:
            logger.error(f"Erreur mise à jour langue : {str(e)}")
            await interaction.response.send_message("❌ Une erreur est survenue lors de la mise à jour de votre langue. Veuillez réessayer.")