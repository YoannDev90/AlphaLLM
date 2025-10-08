import discord
import logging
from utils.config import logger_name, GUILD_ID, OWNER_ID, LOGGER_NAME
from dotenv import load_dotenv
from discord.ext import commands
import os

load_dotenv()

logger = logging.getLogger(logger_name)

async def setup(bot: discord.Client):
    @bot.tree.command(name="reply", description="Répond à un utilisateur via DM")
    async def reply(interaction: discord.Interaction, user_id: str, message: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /reply exécutée par {interaction.user.display_name}")

        if interaction.user.id != OWNER_ID:
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        try:
            user_id = int(user_id)
            asker = await bot.fetch_user(user_id)
            if not OWNER_ID:
                raise ValueError("L'ID du développeur (OWNER_ID) n'est pas défini dans les variables d'environnement.")
            await asker.send(
                f"Développeur (<@{OWNER_ID}>): {message}\nUse `/contact-dev` to reply"
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