import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
from utils.langs import get_translation as tlt
import os

load_dotenv()

logger = logging.getLogger('AlphaLLM')

lang = "en"

async def setup(bot: discord.Client):
    @bot.command(name="announce")
    @commands.is_owner()
    async def announce(ctx: commands.Context, message_id: str):
        """
        Commande pour annoncer un message sur tous les serveurs.
        """

        logger.info(f"Commande announce exécutée par {ctx.author.display_name}")
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            logger.warning("Impossible de supprimer le message de commande. Vérifiez les permissions.")  


        announced_count = 0
        failed_count = 0

        # Vérification du format du message ID
        try:
            message_id = int(message_id)
        except ValueError:
            await ctx.send("ID de message invalide.")
            return

        # Récupération du message dans le canal actuel
        try:
            message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("Message introuvable.")
            return
        except discord.Forbidden:
            await ctx.send("Accès au message refusé.")
            return
        except discord.HTTPException as e:
            await ctx.send(f"Erreur lors de la récupération du message : {str(e)}")
            return

        # Envoi du message sur tous les serveurs
        for guild in bot.guilds:
            try:
                # Trouver un canal approprié dans le serveur
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

                # Envoyer le message dans le canal cible
                await target_channel.send(content=message.content, embeds=message.embeds)
                logger.info(f"Message envoyé sur le serveur {guild.name} dans le canal {target_channel.name}")
                announced_count += 1

            except discord.Forbidden:
                logger.error(f"Permissions insuffisantes pour envoyer un message sur le serveur {guild.name}")
                failed_count += 1
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du message sur le serveur {guild.name}: {str(e)}")
                failed_count += 1

        # Retourner un résumé à l'utilisateur
        await ctx.send(f"Annonce terminée : {announced_count} réussites, {failed_count} échecs.")
