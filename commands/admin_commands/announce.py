import discord
import logging
from utils.config import logger_name
from dotenv import load_dotenv
from utils.server_config import get_announce_channel
from utils.translator import TranslationManager, SUPPORTED_LANGUAGES, load_translations
from embeds.announcement_embed import create_announcement_embed, AnnouncementTranslationView
from embeds.announcement_confirmation_embed import ConfirmationView, create_announcement_confirmation_embed
from utils.command_ids import command_id_manager
from utils.config import logger_name
import os
import json
import aiofiles
from datetime import datetime

load_dotenv()

logger = logging.getLogger(logger_name)
OWNER_ID = int(os.getenv('DEV_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))

class AnnounceModal(discord.ui.Modal, title="Envoyer une annonce"):
    """Modal Discord pour saisir l'annonce - Classe nécessaire pour Discord.py"""
    
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
        self.message = discord.ui.TextInput(
            label="Message d'annonce",
            style=discord.TextStyle.paragraph,
            placeholder="Tapez ici votre annonce en anglais (multi-ligne possible)",
            required=True,
            max_length=2000
        )
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        logger.info(f"Modal soumis par {interaction.user} (ID: {interaction.user.id})")

        if not await check_announce_permission(interaction):
            return

        message = self.message.value
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"translations/announce_{timestamp}.json"
        
        os.makedirs("translations", exist_ok=True)

        await interaction.response.send_message("🔄 Génération des traductions en cours...", ephemeral=True)

        translation_manager = TranslationManager(message, file_path)

        await translation_manager.generate_all_translations(interaction)
        
        confirmation_view = ConfirmationView(message, file_path, translation_manager, len(self.bot.guilds))
        
        # Créer l'embed de confirmation avec aperçu
        embed = discord.Embed(
            title="🔍 Traductions générées - Confirmation requise",
            description=f"**Message original :**\n{message[:1000]}{'...' if len(message) > 1000 else ''}",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="� Statistiques",
            value=f"• **{len(translation_manager.translations)}** langues traduites\n"
                  f"• **Fichier :** `{file_path}`\n"
                  f"• **Serveurs cibles :** {len(self.bot.guilds)}",
            inline=False
        )
        embed.add_field(
            name="🔗 Actions disponibles",
            value="• **Confirmer l'envoi** : Envoie l'annonce sur tous les serveurs\n"
                  f"• **Aperçu traductions** : Voir quelques exemples de traductions",
            inline=False
        )
        embed.set_footer(text="⚠️ Vérifiez les traductions avant d'envoyer l'annonce")
        
        await interaction.edit_original_response(
            content=None,
            embed=embed,
            view=confirmation_view
        )

async def check_announce_permission(interaction: discord.Interaction) -> bool:
    if interaction.user.id != OWNER_ID:
        logger.warning(f"Refus d'accès pour {interaction.user} (ID: {interaction.user.id})")
        await interaction.response.send_message(
            "Vous n'avez pas la permission d'utiliser cette commande.", 
            ephemeral=True
        )
        return False
    return True

async def find_announcement_channel(guild):
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

    return target_channel, ask_define

async def send_announcement_to_guilds(bot, message: str, translation_view: AnnouncementTranslationView) -> tuple[int, int]:
    embed = create_announcement_embed(message, 'en')

    announced_guilds = 0
    failed_guilds = 0

    logger.info(f"Début de l'envoi de l'annonce sur tous les serveurs")
    
    for guild in bot.guilds:
        logger.info(f"Traitement du serveur : {guild.name} (ID: {guild.id})")
        
        try:
            target_channel, ask_define = await find_announcement_channel(guild)

            if not target_channel:
                logger.warning(f"Aucun canal d'annonce trouvé sur le serveur {guild.name} (ID: {guild.id})")
                failed_guilds += 1
                continue

            await target_channel.send(embed=embed, view=translation_view)
            logger.info(f"Annonce envoyée sur {guild.name} dans {target_channel.name}")
            announced_guilds += 1

            if ask_define:
                await send_channel_config_suggestion(target_channel, guild)

        except discord.Forbidden:
            logger.error(f"Permissions insuffisantes pour envoyer un message sur le serveur {guild.name} (ID: {guild.id})")
            failed_guilds += 1
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi sur {guild.name} (ID: {guild.id}) : {e}")
            failed_guilds += 1

    logger.info(f"Annonce terminée : {announced_guilds} serveurs réussis, {failed_guilds} échecs")
    
    return announced_guilds, failed_guilds

async def send_channel_config_suggestion(target_channel, guild):
    logger.info(f"Demande de configuration du canal d'annonce sur {guild.name} (ID: {guild.id})")
    await target_channel.send(
        f"<@{guild.owner_id}> Veuillez configurer ce canal comme canal d'annonces avec la commande "
        f"{command_id_manager.get_command_mention('guild-config')} ou utilisez {target_channel.mention} par défaut."
    )

async def send_final_report(interaction, announced_guilds: int, failed_guilds: int, 
                           translation_view: AnnouncementTranslationView, file_path: str):
    await interaction.followup.send(
        f"✅ **Annonce terminée avec succès !**\n"
        f"• **{announced_guilds} serveurs** : annonce envoyée\n"
        f"• **{failed_guilds} serveurs** : échecs\n"
        f"• **Traductions** : {len(translation_view.original_message)} caractères générés\n"
        f"• **Fichier** : `{file_path}`",
        ephemeral=True
    )

async def setup_persistent_views(bot):
    if not os.path.exists("translations"):
        return
    
    files = os.listdir("translations")
    
    for filename in files:
        if not (filename.startswith("announce_") and filename.endswith(".json")):
            continue
            
        file_path = os.path.join("translations", filename)
        
        try:
            original_message, translations = await load_translations(file_path)
            if not original_message:
                continue
            
            view = AnnouncementTranslationView(original_message, file_path)
            bot.add_view(view)
            logger.info(f"Vue persistante restaurée pour {filename}")
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de la vue pour {filename}: {e}")

async def setup(bot: discord.Client):
    await setup_persistent_views(bot)
    
    @bot.tree.command(name="announce", description="Annonce un message sur tous les serveurs")
    async def announce(interaction: discord.Interaction):
        modal = AnnounceModal(bot)
        await interaction.response.send_modal(modal)
