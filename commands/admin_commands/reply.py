import discord
from utils.config import DEV_IDS, LOGGER_NAME, is_dev_id
from utils.core.logger import get_logger

logger = get_logger(LOGGER_NAME)

async def setup(bot: discord.Client):
    @bot.tree.command(name="reply", description="Répond à un utilisateur via DM")
    async def reply(interaction: discord.Interaction, user_id: str, message: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /reply exécutée par {interaction.user.display_name}")

        if not is_dev_id(interaction.user.id):
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        try:
            user_id = int(user_id)
            asker = await bot.fetch_user(user_id)
            if not DEV_IDS:
                raise ValueError("Les IDs des développeurs ne sont pas définis dans la configuration.")
            await asker.send(
                f"Développeur (<@{interaction.user.id}>): {message}\nUse `/contact-dev` to reply"
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