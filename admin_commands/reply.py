import discord
import logging
from dotenv import load_dotenv
from discord.ext import commands
from utils.langs import get_translation as tlt
import os

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger('AlphaLLM')
OWNER_ID = int(os.getenv('DEV_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))

async def setup(bot: discord.Client):
    @bot.tree.command(name="reply", description="Envoie un message privé à un utilisateur")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def reply(interaction: discord.Interaction, user_id: int, message: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /reply exécutée par {interaction.user.display_name}")

        if interaction.user.id != OWNER_ID:
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        try:
            asker = await bot.fetch_user(user_id)
            dev_id = os.getenv("DEV_ID")
            if not dev_id:
                raise ValueError("L'ID du développeur (DEV_ID) n'est pas défini dans les variables d'environnement.")
            await asker.send(
                f"Développeur (<@{dev_id}>): {message}\nUse `/contact` to reply"
            )
        except discord.HTTPException as e:
            logger.error(f"Erreur lors de l'envoi du message : {e}")
            await interaction.followup.send("Erreur lors de l'envoi du message.", ephemeral=True)
            return
        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            await interaction.followup.send("Erreur inattendue.", ephemeral=True)
            return

        await interaction.followup.send("Message envoyé avec succès.", ephemeral=True)