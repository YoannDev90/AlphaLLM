import discord
import logging
from dotenv import load_dotenv
from utils.langs import get_translation as tlt
import os

load_dotenv()

logger = logging.getLogger('AlphaLLM')

lang = "en"

async def setup(bot: discord.Client):
    @bot.tree.command(name="announce", description="Annonce un message sur tous les serveurs")
    async def announce(interaction: discord.Interaction, message_id: str):
        logger.info(f"Commande announce exécutée par {interaction.user.display_name} pour le message ID {message_id}")
        if not str(interaction.user.id) == os.getenv("DEV_ID"):
            await interaction.response.send_message(tlt(language=lang, key="admin_command_not_authorized"), ephemeral=True)
            return
        announced_count = 0
        failed_count = 0
        await interaction.response.defer()

        try:
            message_id = int(message_id)
        except ValueError:
            await interaction.response.send_message(tlt(language=lang, key="invalid_message_id"), ephemeral=True)
            return

        try:
            message = await interaction.channel.fetch_message(message_id)
        except discord.NotFound:
            await interaction.response.send_message(tlt(language=lang, key="message_not_found"), ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.response.send_message(tlt(language=lang, key="message_access_denied"), ephemeral=True)
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(tlt(language=lang, key="other_exception", e=str(e)), ephemeral=True)
            return

        for guild in bot.guilds:
            try:
                target_channel = None
                for channel in guild.text_channels:
                    permissions = channel.permissions_for(guild.default_role)
                    if permissions.read_messages and permissions.send_messages:
                        target_channel = channel
                        break

                if target_channel is None:
                    target_channel = guild.system_channel

                if target_channel is None:
                    logger.warning(f"Aucun canal approprié trouvé sur le serveur {guild.name}")
                    failed_count += 1
                    continue

                await target_channel.send(content=message.content, embeds=message.embeds, files=[await f.to_file() for f in message.attachments])
                logger.info(f"Message envoyé sur le serveur {guild.name} dans le canal {target_channel.name}")
                announced_count += 1

            except discord.Forbidden:
                logger.error(f"Permissions insuffisantes pour envoyer un message sur le serveur {guild.name}")
                failed_count += 1
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du message sur le serveur {guild.name}: {e}")
                failed_count += 1

        await interaction.followup.send(tlt(language=lang, key="announce_finished", announced_count=announced_count, failed_count=failed_count))