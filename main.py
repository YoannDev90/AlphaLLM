import asyncio
import warnings
import json
import datetime
import sys
import os
import signal
from bots.bot import run_bot
from bots.admin_bot import run_admin_bot
from bots.logger_bot import run_logger_bot
from bots.mistral_bot import run_mistral_bot
from bots.gemini_bot import run_gemini_bot
from bots.evilgpt_bot import run_evilgpt_bot
from bots.llama_bot import run_llama_bot
from bots.chatgpt_bot import run_chatgpt_bot
from bots.deepseek_bot import run_deepseek_bot
from bots.grok_bot import run_grok_bot
from bots.perplexity_bot import run_perplexity_bot
from bots.qwen_bot import run_qwen_bot
from bots.claude_bot import run_claude_bot
from bots.phi_bot import run_phi_bot
from bots.kimi_bot import run_kimi_bot
from bots.glm_bot import run_glm_bot
from bots.command_bot import run_command_bot
from api.api import start_api_async
from api.utils.server_utils import ping_https_server
from utils.config import LOGGER_NAME, get_logging_level, API_URL
import logging

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(get_logging_level())

# Variable globale pour gérer l'arrêt propre
shutdown_event = asyncio.Event()
restart_requested = False

def handle_shutdown_signal(signum, frame):
    """Gestionnaire de signal pour arrêt propre"""
    global restart_requested
    logger.debug(f"Signal {signum} reçu, arrêt en cours...")
    
    # Vérifie si c'est un redémarrage ou un arrêt
    command = check_restart_command()
    logger.debug(f"Commande lue depuis stop.json: {command}")
    restart_requested = (command == "RESTART")
    logger.debug(f"Redémarrage demandé: {restart_requested}")
    
    # Déclenche l'événement d'arrêt
    try:
        loop = asyncio.get_running_loop()
        logger.debug("Event loop trouvée, déclenchement de shutdown_event")
        loop.call_soon_threadsafe(shutdown_event.set)
        logger.debug("shutdown_event.set() appelé")
    except RuntimeError as e:
        logger.error(f"Impossible de récupérer l'event loop: {e}")

def check_restart_command():
    """Vérifie si un redémarrage ou arrêt a été demandé"""
    try:
        with open("stop.json", "r") as f:
            data = json.load(f)
            command = data.get("COMMAND")
            timestamp = datetime.datetime.fromisoformat(data["timestamp"])
            
            # Vérifie que la commande n'est pas trop ancienne (évite les boucles)
            if datetime.datetime.now() - timestamp > datetime.timedelta(minutes=1):
                os.remove("stop.json")
                return None
            
            return command
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None

async def main():
    # Configure les gestionnaires de signaux
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    
    # Crée une tâche pour surveiller le fichier stop.json
    async def monitor_stop_file():
        """Surveille le fichier stop.json pour détecter les demandes d'arrêt"""
        while not shutdown_event.is_set():
            try:
                if os.path.exists("stop.json"):
                    command = check_restart_command()
                    if command in ["STOP", "RESTART"]:
                        logger.debug(f"Commande {command} détectée dans stop.json")
                        # Déclenche l'arrêt
                        os.kill(os.getpid(), signal.SIGTERM)
                        break
            except Exception as e:
                logger.error(f"Erreur lors de la surveillance du fichier stop.json: {e}")
            await asyncio.sleep(1)
    
    # Wrapper pour arrêter les bots quand shutdown_event est déclenché
    async def run_with_shutdown(coro, name="task"):
        """Execute une coroutine et l'annule quand shutdown_event est set"""
        task = asyncio.create_task(coro)
        
        # Attend soit la fin de la tâche, soit le shutdown
        done, pending = await asyncio.wait(
            [task, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Si shutdown_event est déclenché, annule la tâche
        if shutdown_event.is_set():
            logger.debug(f"Arrêt de la tâche: {name}")
            task.cancel()
            try:
                # Laisse 2 secondes pour terminer proprement
                await asyncio.wait_for(task, timeout=2.0)
            except asyncio.CancelledError:
                logger.debug(f"Tâche {name} annulée proprement")
            except asyncio.TimeoutError:
                logger.warning(f"Tâche {name} n'a pas pu se terminer dans le délai")
            except Exception as e:
                logger.error(f"Erreur lors de l'arrêt de {name}: {e}")
        
        return task.result() if task.done() and not task.cancelled() else None
    
    try:        
        await asyncio.gather(
            monitor_stop_file(),
            run_with_shutdown(start_api_async(), "API"),
            run_with_shutdown(ping_https_server(API_URL), "Ping HTTPS"),
            run_with_shutdown(run_bot(), "Bot principal"),
            run_with_shutdown(run_admin_bot(), "Admin Bot"),
            run_with_shutdown(run_logger_bot(), "Logger Bot"),
            run_with_shutdown(run_mistral_bot(), "Mistral Bot"),
            run_with_shutdown(run_gemini_bot(), "Gemini Bot"),
            run_with_shutdown(run_evilgpt_bot(), "EvilGPT Bot"),
            run_with_shutdown(run_llama_bot(), "Llama Bot"),
            run_with_shutdown(run_chatgpt_bot(), "ChatGPT Bot"),
            run_with_shutdown(run_deepseek_bot(), "DeepSeek Bot"),
            run_with_shutdown(run_grok_bot(), "Grok Bot"),
            run_with_shutdown(run_perplexity_bot(), "Perplexity Bot"),
            run_with_shutdown(run_qwen_bot(), "Qwen Bot"),
            run_with_shutdown(run_claude_bot(), "Claude Bot"),
            run_with_shutdown(run_phi_bot(), "Phi Bot"),
            run_with_shutdown(run_kimi_bot(), "Kimi Bot"),
            run_with_shutdown(run_glm_bot(), "GLM Bot"),
            run_with_shutdown(run_command_bot(), "Command Bot"),
            return_exceptions=True
        )

    except (SystemExit, KeyboardInterrupt):
        logger.info("Arrêt complet du programme.")
    except Exception as e:
        logger.error(f"Erreur non gérée : {str(e)}")
    finally:
        logger.debug("Entrée dans le bloc finally de main()")
        # Annule et attend toutes les tâches restantes pour éviter les warnings
        pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        logger.debug(f"Nombre de tâches en attente: {len(pending)}")
        if pending:
            for task in pending:
                task.cancel()
            try:
                logger.debug("Attente de la fin des tâches annulées...")
                await asyncio.gather(*pending, return_exceptions=True)
                logger.debug("Toutes les tâches ont été annulées et attendues.")
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage des tâches: {str(e)}")
        logger.info("Nettoyage terminé.")

if __name__ == "__main__":
    # Vérifie si un arrêt a été demandé au démarrage
    command = check_restart_command()
    if command == "STOP":
        logger.info("Arrêt demandé via stop.json. Le bot ne démarrera pas.")
        try:
            os.remove("stop.json")
        except Exception:
            pass
        sys.exit(0)
    
    # Supprime le fichier stop.json s'il existe pour éviter les conflits
    try:
        if os.path.exists("stop.json"):
            os.remove("stop.json")
    except Exception as e:
        logger.warning(f"Impossible de supprimer stop.json: {e}")
    
    # Lance le bot
    try:
        logger.debug("Lancement de asyncio.run(main())...")
        asyncio.run(main())
        logger.debug("asyncio.run(main()) terminé.")
    except KeyboardInterrupt:
        logger.debug("Interruption manuelle - Arrêt du programme.")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)
    
    # Vérifie après la sortie complète si un redémarrage est demandé
    logger.debug(f"Vérification du redémarrage: restart_requested = {restart_requested}")
    if restart_requested:
        logger.info("Redémarrage demandé. Relance du processus...")
        try:
            os.remove("stop.json")
        except Exception:
            pass
        # Relance le processus
        logger.debug(f"Exécution de os.execv({sys.executable}, {[sys.executable] + sys.argv})")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    logger.info("Arrêt complet du bot.")
