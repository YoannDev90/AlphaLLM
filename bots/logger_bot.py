import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.logger_utils import setup_logging
from utils.config import update_log_level, get_current_log_level
import asyncio
import datetime
import sys

load_dotenv()

LOGGER_TOKEN = os.getenv("LOGGER_BOT_TOKEN")
LOGGER_PREFIX = os.getenv("LOGGER_BOT_PREFIX")

intents = discord.Intents.default()

logger_bot = commands.Bot(command_prefix=LOGGER_PREFIX, intents=intents)
logger = setup_logging(logger_bot)

@logger_bot.event
async def on_ready():
    activity = discord.CustomActivity(name="🎛️ Monitoring AlphaLLM")
    await logger_bot.change_presence(activity=activity)
    await logger_bot.tree.sync()
    while True:
        await auto_purge()
        await asyncio.sleep(60)

async def auto_purge():
    try:
        dev_id = os.getenv("DEV_ID")
        dev_user = await logger_bot.fetch_user(dev_id)
        dm_channel = await dev_user.create_dm()
        
        cutoff_time = discord.utils.utcnow() - datetime.timedelta(days=2.0)
        deleted_count = 0
        
        async for message in dm_channel.history(limit=None, before=cutoff_time):
            try:
                await message.delete()
                deleted_count += 1
            except discord.NotFound:
                continue
            except discord.HTTPException:
                continue
                
    except discord.HTTPException as e:
        logger.error(f"Erreur lors de la purge : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'auto-purge : {e}")

@logger_bot.tree.command(name="clear", description="Purge tous les messages DM sans limite de temps")
async def clear_command(interaction: discord.Interaction):
    try:
        dev_id = os.getenv("DEV_ID")
        if str(interaction.user.id) != dev_id:
            await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        dev_user = await logger_bot.fetch_user(dev_id)
        dm_channel = await dev_user.create_dm()
        
        deleted_count = 0
        async for message in dm_channel.history(limit=None):
            try:
                await message.delete()
                deleted_count += 1
            except discord.NotFound:
                continue
            except discord.HTTPException:
                continue
        
        await interaction.followup.send(f"✅ {deleted_count} messages supprimés avec succès.", ephemeral=True)
        logger.info(f"Commande /clear exécutée : {deleted_count} messages supprimés")
        
    except discord.HTTPException as e:
        logger.error(f"Erreur lors de la purge manuelle : {e}")
        await interaction.followup.send(f"❌ Erreur lors de la purge : {e}", ephemeral=True)
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la commande /clear : {e}")
        await interaction.followup.send(f"❌ Erreur inattendue : {e}", ephemeral=True)

@logger_bot.tree.command(name="loglevel", description="Modifier le niveau de logging et redémarrer le bot")
@discord.app_commands.describe(level="Nouveau niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
async def loglevel_command(interaction: discord.Interaction, level: str):
    """Commande pour modifier le niveau de logging dans config.toml et redémarrer le bot"""
    try:
        dev_id = os.getenv("DEV_ID")
        if str(interaction.user.id) != dev_id:
            await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Validation du niveau
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level_upper = level.upper()
        
        if level_upper not in valid_levels:
            await interaction.followup.send(
                f"❌ Niveau de log invalide. Niveaux disponibles : {', '.join(valid_levels)}", 
                ephemeral=True
            )
            return
        
        # Récupérer le niveau actuel
        current_level = get_current_log_level()
        
        if current_level and current_level.upper() == level_upper:
            await interaction.followup.send(
                f"ℹ️ Le niveau de log est déjà défini sur {level_upper}.", 
                ephemeral=True
            )
            return
        
        # Mettre à jour le niveau de log
        if update_log_level(level_upper):
            await interaction.followup.send(
                f"✅ Niveau de log modifié de {current_level or 'INCONNU'} vers {level_upper}.\n" +
                "🔄 Redémarrage du bot en cours...", 
                ephemeral=True
            )
            
            logger.info(f"Commande /loglevel exécutée : {current_level} -> {level_upper}")
            logger.info("Redémarrage du bot Logger...")
            
            # Fermer le bot proprement
            await logger_bot.close()
            
            # Redémarrer le processus
            os.execv(sys.executable, ['python'] + sys.argv)
            
        else:
            await interaction.followup.send(
                "❌ Erreur lors de la modification du fichier de configuration.", 
                ephemeral=True
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la commande /loglevel : {e}")
        await interaction.followup.send(f"❌ Erreur inattendue : {e}", ephemeral=True)

@loglevel_command.autocomplete('level')
async def loglevel_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[discord.app_commands.Choice[str]]:
    """Autocompletion pour les niveaux de logging"""
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    return [
        discord.app_commands.Choice(name=level, value=level)
        for level in levels if current.upper() in level
    ]

async def run_logger_bot():
    try:
        await logger_bot.start(LOGGER_TOKEN)
    except discord.LoginFailure as e:
        logger.error(f"Erreur de connexion : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        await logger_bot.close()
    finally:
        logger.info("Arrêt du bot Logger.")
        raise SystemExit(0)
