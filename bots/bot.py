import discord
from discord.ext import commands
import logging
import datetime
from commands.cmds import setup_commands
from utils.ai_process import process_ai_response
from utils.database import get_blacklist
from utils.database import get_supabase_client
from utils.config import DEBUG, GUILD_ID, OWNER_ID, get_bot_token, LOGGER_NAME
from utils.server_config import update_all_guilds_info
from embeds.welcome import create_welcome_embed, WelcomeLanguageView
from utils.command_ids import command_id_manager
from utils.msg_process import message_process

TOKEN = get_bot_token()
GUILD_ID = GUILD_ID

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", owner_id=OWNER_ID, intents=intents)

supabase = get_supabase_client()
logger = logging.getLogger(LOGGER_NAME)

@bot.event
async def on_ready():
    activity = discord.CustomActivity(name="🤖 Try @AlphaLLM or /commands")
    await bot.change_presence(activity=activity, status=discord.Status.idle)
    await bot.tree.sync()
    
    # Initialiser le gestionnaire d'IDs de commandes
    command_id_manager.set_bot(bot)
    await command_id_manager.fetch_command_ids()
    try:
        await update_all_guilds_info(bot)
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des serveurs: {e}")

@bot.event
async def on_guild_join(guild):
    logger.info(f"Bot ajouté au serveur: {guild.name} (ID: {guild.id})")

    try:
        # Créer l'embed de bienvenue en anglais par défaut
        embed = create_welcome_embed(bot, guild, 'en')

        # Créer la vue avec les boutons de langues
        view = WelcomeLanguageView(bot)
        
        target_channel = None
        
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            target_channel = guild.system_channel

        if not target_channel:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    target_channel = channel
                    break
        
        if target_channel:
            await target_channel.send(embed=embed, view=view)
            logger.info(f"Message de bienvenue envoyé sur {guild.name} dans {target_channel.name}")
        else:
            logger.warning(f"Aucun canal accessible trouvé sur {guild.name} pour envoyer le message de bienvenue")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message de bienvenue sur {guild.name}: {e}")


@bot.event
async def on_guild_remove(guild):
    try:
        logger.info(f"Bot retiré du serveur: {guild.name} (ID: {guild.id})")
        
        from utils.server_config import delete_server_settings
        delete_server_settings(guild.id)
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du serveur {guild.name}: {e}")

@bot.event
async def on_message(message):
    await message_process(bot, message)

async def run_bot():
    logger.info("Démarrage ...")
    await setup_commands(bot, is_admin_bot=False)
    try:
        await bot.start(TOKEN)
    except discord.LoginFailure as e:
        logger.error(f"Erreur de connexion : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        await bot.close()
    finally:
        logger.info("Arrêt du bot.")
        raise SystemExit(0)