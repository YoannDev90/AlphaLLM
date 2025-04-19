import discord
import logging
from dotenv import load_dotenv
from utils.user_config import get_announce_mp_active
from utils.server_config import get_announce_channel
from utils.langs import get_language, get_translation as tlt
import os

load_dotenv()
logger = logging.getLogger('AlphaLLM')
OWNER_ID = int(os.getenv('DEV_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))

async def setup(bot: discord.Client):
    @bot.tree.command(name="announce", description="Annonce un message sur tous les serveurs")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def announce(interaction: discord.Interaction, message_id: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(f"Commande /announce exécutée par {interaction.user.display_name}")

        if interaction.user.id != OWNER_ID:
            await interaction.followup.send("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        try:
            message_id_int = int(message_id)
        except ValueError:
            await interaction.followup.send("ID de message invalide.", ephemeral=True)
            return

        try:
            message = await interaction.channel.fetch_message(message_id_int)
        except discord.NotFound:
            await interaction.followup.send("Message introuvable.", ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.followup.send("Accès au message refusé.", ephemeral=True)
            return
        except discord.HTTPException as e:
            await interaction.followup.send(f"Erreur lors de la récupération du message : {str(e)}", ephemeral=True)
            return

        announced_guilds = 0
        failed_guilds = 0
        announced_users = 0
        failed_users = 0

        # Annonce en MP à l'owner si activé
        if get_announce_mp_active(interaction.user.id):
            try:
                await interaction.user.send(message.content, embeds=message.embeds)
                logger.info(f"Annonce envoyée en MP à {interaction.user.display_name}")
                announced_users += 1
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'annonce en MP à l'owner : {e}")
                failed_users += 1

        for guild in bot.guilds:
            try:
                announce_channel_id = get_announce_channel(guild.id)
                target_channel = None
                ask_define = False

                # Priorité au canal d'annonce configuré
                if announce_channel_id:
                    target_channel = guild.get_channel(announce_channel_id)
                    ask_define = False

                # Sinon, canal système si accessible
                if not target_channel and guild.system_channel:
                    perms = guild.system_channel.permissions_for(guild.me)
                    if perms.read_messages and perms.send_messages:
                        target_channel = guild.system_channel
                        ask_define = True

                # Sinon, premier canal textuel accessible
                if not target_channel:
                    for channel in guild.text_channels:
                        perms = channel.permissions_for(guild.me)
                        if perms.read_messages and perms.send_messages:
                            target_channel = channel
                            ask_define = True
                            break

                if not target_channel:
                    logger.warning(f"Aucun canal d'annonce trouvé sur le serveur {guild.name} ({guild.id})")
                    failed_guilds += 1
                    continue

                # Envoi de l'annonce
                await target_channel.send(content=message.content, embeds=message.embeds)

                # Si canal non configuré, demande la configuration au propriétaire du serveur
                if ask_define:
                    logger.info(f"Demande de configuration du canal d'annonce sur {guild.name} ({guild.id})")
                    await target_channel.send(
                        f"<@{guild.owner_id}> " +
                        tlt(get_language(guild.owner_id), "ask_define_announce_channel").format(
                            channel=target_channel.mention
                        )
                    )

                logger.info(f"Annonce envoyée sur {guild.name} dans {target_channel.name}")
                announced_guilds += 1

            except discord.Forbidden:
                logger.error(f"Permissions insuffisantes pour envoyer un message sur le serveur {guild.name}")
                failed_guilds += 1
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi sur {guild.name}: {e}")
                failed_guilds += 1

        await interaction.followup.send(
            f"Annonce terminée :\n"
            f"- Serveurs : {announced_guilds} réussites, {failed_guilds} échecs\n"
            f"- Utilisateurs (MP) : {announced_users} réussites, {failed_users} échecs",
            ephemeral=True
        )
