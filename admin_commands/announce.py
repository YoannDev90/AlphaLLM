import discord
import logging
from dotenv import load_dotenv
from utils.user_config import get_announce_mp_active
from utils.server_config import get_announce_channel
from utils.langs import get_language, get_translation as tlt
from utils.translator import translate_announcement_guild, translate_announcement_mp
import os

load_dotenv()
logger = logging.getLogger('AlphaLLM')
OWNER_ID = int(os.getenv('DEV_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))

class AnnounceModal(discord.ui.Modal, title="Envoyer une annonce"):
    message = discord.ui.TextInput(
        label="Message d'annonce",
        style=discord.TextStyle.paragraph,
        placeholder="Tapez ici votre annonce (multi-ligne possible)",
        required=True,
        max_length=2000
    )

    def __init__(self, bot, interaction):
        super().__init__()
        self.bot = bot
        self.interaction = interaction  # Pour vérifier l'auteur

    async def on_submit(self, interaction: discord.Interaction):
        logger.info(f"Modal soumis par {interaction.user} (ID: {interaction.user.id})")

        if interaction.user.id != OWNER_ID:
            logger.warning(f"Refus d'accès pour {interaction.user} (ID: {interaction.user.id})")
            await interaction.response.send_message("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        message = self.message.value

        announced_guilds = 0
        failed_guilds = 0
        announced_users = 0
        failed_users = 0

        logger.info(f"Début de l'envoi de l'annonce en MP à tous les utilisateurs")
        for user in self.bot.users:
            if user.bot or user.id == self.bot.user.id:
                logger.debug(f"Utilisateur ignoré (bot ou self) : {user} (ID: {user.id})")
                continue
            if get_announce_mp_active(user.id):
                logger.debug(f"Envoi MP activé pour {user} (ID: {user.id})")
                try:
                    translated_content = await translate_announcement_mp(message, user)
                    logger.info(f"Contenu traduit pour {user.display_name} (ID: {user.id})")
                    if translated_content:
                        await user.send(translated_content)
                        logger.info(f"Annonce envoyée en MP à {user.display_name} (ID: {user.id})")
                        announced_users += 1
                    else:
                        logger.warning(f"Message vide, non envoyé à {user.display_name} (ID: {user.id})")
                        failed_users += 1
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi de l'annonce en MP à {user.display_name} (ID: {user.id}) : {e}")
                    failed_users += 1
            else:
                logger.debug(f"Envoi MP désactivé pour {user} (ID: {user.id})")

        logger.info(f"Début de l'envoi de l'annonce sur tous les serveurs")
        for guild in self.bot.guilds:
            logger.info(f"Traitement du serveur : {guild.name} (ID: {guild.id})")
            try:
                announce_channel_id = get_announce_channel(guild.id)
                target_channel = None
                ask_define = False

                if announce_channel_id:
                    target_channel = guild.get_channel(announce_channel_id)
                    logger.info(f"Canal d'annonce configuré trouvé : {target_channel} (ID: {announce_channel_id})")
                    ask_define = False

                if not target_channel and guild.system_channel:
                    perms = guild.system_channel.permissions_for(guild.me)
                    if perms.read_messages and perms.send_messages:
                        target_channel = guild.system_channel
                        logger.info(f"Utilisation du canal système : {target_channel}")
                        ask_define = True

                if not target_channel:
                    for channel in guild.text_channels:
                        perms = channel.permissions_for(guild.me)
                        if perms.read_messages and perms.send_messages:
                            target_channel = channel
                            logger.info(f"Utilisation du premier canal accessible : {target_channel}")
                            ask_define = True
                            break

                if not target_channel:
                    logger.warning(f"Aucun canal d'annonce trouvé sur le serveur {guild.name} (ID: {guild.id})")
                    failed_guilds += 1
                    continue

                translated_content = await translate_announcement_guild(message, guild)
                logger.info(f"Contenu traduit pour {guild.name}")
                if translated_content:
                    await target_channel.send(content=translated_content)
                    logger.info(f"Annonce envoyée sur {guild.name} dans {target_channel.name}")
                    announced_guilds += 1
                else:
                    logger.warning(f"Message vide, non envoyé sur {guild.name} (ID: {guild.id})")
                    failed_guilds += 1

                if ask_define:
                    logger.info(f"Demande de configuration du canal d'annonce sur {guild.name} (ID: {guild.id})")
                    await target_channel.send(
                        f"<@{guild.owner_id}> " +
                        tlt(get_language(guild.owner_id), "ask_define_announce_channel").format(
                        channel=target_channel.mention
                        )
                    )

            except discord.Forbidden:
                logger.error(f"Permissions insuffisantes pour envoyer un message sur le serveur {guild.name} (ID: {guild.id})")
                failed_guilds += 1
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi sur {guild.name} (ID: {guild.id}) : {e}")
                failed_guilds += 1

        logger.info(f"Annonce terminée : {announced_guilds} serveurs réussis, {failed_guilds} échecs, {announced_users} utilisateurs MP, {failed_users} échecs MP")
        await interaction.response.send_message(
            f"Annonce terminée :\n"
            f"- Serveurs : {announced_guilds} réussites, {failed_guilds} échecs\n"
            f"- Utilisateurs (MP) : {announced_users} réussites, {failed_users} échecs",
            ephemeral=True
        )

async def setup(bot: discord.Client):
    @bot.tree.command(name="announce", description="Annonce un message sur tous les serveurs")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def announce(interaction: discord.Interaction):
        modal = AnnounceModal(bot, interaction)
        await interaction.response.send_modal(modal)
