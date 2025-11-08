import asyncio
import json
import datetime
import sys
import os
import signal
import logging

os.environ["LITELLM_LOG"] = "CRITICAL" 

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
from utils.config.app_config import (
    LOGGER_NAME, get_logging_level, API_URL,
    LAUNCHER_RUN_API, LAUNCHER_RUN_MAIN_BOT, LAUNCHER_RUN_SECONDARY_BOTS,
    LAUNCHER_RUN_ADMIN_BOT, LAUNCHER_RUN_LOGGER_BOT
)
from utils.monitoring.resource import start_monitoring, stop_monitoring, get_default_monitor
from utils.monitoring.exporter import start_exporter, stop_exporter

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.INFO)

shutdown_event = asyncio.Event()
restart_requested = False

def handle_shutdown_signal(signum, frame):
    """Gestionnaire de signal pour arrêt propre"""
    global restart_requested
    logger.debug(f"Signal {signum} reçu (frame: {frame}), arrêt en cours...")
    
    logger.debug("Vérification de la commande dans stop.json...")
    command = check_restart_command()
    logger.debug(f"Commande lue depuis stop.json: {command}")
    restart_requested = (command == "RESTART")
    logger.debug(f"Redémarrage demandé: {restart_requested}")
    
    try:
        loop = asyncio.get_running_loop()
        logger.debug("Event loop trouvée, déclenchement de shutdown_event")
        loop.call_soon_threadsafe(shutdown_event.set)
        logger.debug("shutdown_event.set() appelé avec succès")
    except RuntimeError as e:
        logger.error(f"Impossible de récupérer l'event loop: {e}")
        logger.debug(f"RuntimeError lors de la récupération de l'event loop: {e}", exc_info=True)

def check_restart_command():
    """Vérifie si un redémarrage ou arrêt a été demandé"""
    try:
        with open("stop.json", "r") as f:
            data = json.load(f)
            command = data.get("COMMAND")
            timestamp = datetime.datetime.fromisoformat(data["timestamp"])
            
            if datetime.datetime.now() - timestamp > datetime.timedelta(minutes=1):
                logger.debug("Timestamp trop ancien (>1 minute), suppression du fichier")
                os.remove("stop.json")
                return None
            
            return command
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        logger.debug(f"Erreur JSON lors de la lecture de stop.json: {e}")
        return None
    except KeyError as e:
        logger.debug(f"Clé manquante dans stop.json: {e}")
        return None
    except Exception as e:
        logger.debug(f"Exception inattendue lors de la lecture de stop.json: {e}", exc_info=True)
        return None

async def main():
    logger.debug("Initialisation de la fonction main()")
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    logger.debug("Gestionnaires de signal configurés")

    async def monitor_stop_file():
        """Surveille le fichier stop.json pour détecter les demandes d'arrêt (tous les 30s)"""
        logger.debug("Démarrage du moniteur de fichier stop.json")
        while not shutdown_event.is_set():
            try:
                if os.path.exists("stop.json"):
                    command = check_restart_command()
                    if command in ["STOP", "RESTART"]:
                        logger.info(f"Commande {command} détectée dans stop.json")
                        logger.debug(f"Envoi du signal SIGTERM au PID {os.getpid()}")
                        os.kill(os.getpid(), signal.SIGTERM)
                        break
            except Exception as e:
                logger.error(f"Erreur lors de la surveillance du fichier stop.json: {e}")
                logger.debug(f"Exception complète lors de la surveillance: {e}", exc_info=True)
            
            await asyncio.sleep(30)
        
        logger.debug("Moniteur de fichier stop.json arrêté")
    
    async def log_resource_usage():
        """Enregistre périodiquement l'utilisation des ressources"""
        logger.debug("Démarrage du logger de ressources")
        monitor = get_default_monitor()
        
        while not shutdown_event.is_set():
            try:
                snapshot = monitor.get_latest_snapshot()
                if snapshot:
                    stats = monitor.get_statistics()
                    if stats:
                        logger.debug(
                            f"Resources - CPU: {snapshot.cpu_time:.2f}s | "
                            f"Memory: {snapshot.max_memory:.1f}MB | "
                            f"Avg Memory: {stats.get('memory_avg', 0):.1f}MB"
                        )
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement des ressources: {e}")
            
            if shutdown_event.is_set():
                break
        
        logger.debug("Logger de ressources arrêté")
    
    async def run_with_shutdown(coro, name="task"):
        """Execute une coroutine et l'annule quand shutdown_event est set"""
        logger.debug(f"Création de la tâche: {name}")
        task = asyncio.create_task(coro)
        
        done, pending = await asyncio.wait(
            [task, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        if shutdown_event.is_set():
            logger.debug(f"Arrêt de la tâche: {name}")
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=2.0)
            except asyncio.CancelledError:
                logger.debug(f"Tâche {name} annulée proprement")
            except asyncio.TimeoutError:
                logger.warning(f"Tâche {name} n'a pas pu se terminer dans le délai")
            except Exception as e:
                logger.error(f"Erreur lors de l'arrêt de {name}: {e}")
        
        return task.result() if task.done() and not task.cancelled() else None
    
    try:
        logger.debug("Construction de la liste des tâches à lancer")
        tasks = [monitor_stop_file()]
        logger.debug("Moniteur de fichier stop.json ajouté")
        
        logger.info("Démarrage du monitoring des ressources...")
        monitor = start_monitoring(interval=1.0)
        tasks.append(run_with_shutdown(log_resource_usage(), "Resource Logger"))
        logger.debug(f"✓ Resource Monitor démarré (PID: {os.getpid()}, interval: 1s)")
        
        logger.debug("Démarrage de l'export CSV des ressources...")
        exporter = await start_exporter(
            csv_filename="resources.csv",
            collection_interval=1.0,
            export_interval=15.0
        )
        logger.debug("✓ Resource Exporter démarré (collect: 1s, export: 15s)")
        
        if LAUNCHER_RUN_API:
            logger.debug("Ajout de l'API aux tâches")
            tasks.append(run_with_shutdown(start_api_async(), "API"))
            tasks.append(run_with_shutdown(ping_https_server(API_URL), "Ping HTTPS"))
            logger.debug("API et Ping HTTPS ajoutés")
        
        if LAUNCHER_RUN_MAIN_BOT:
            logger.debug("Ajout du bot principal aux tâches")
            tasks.append(run_with_shutdown(run_bot(), "Bot principal"))
            logger.debug("Bot principal ajouté")
        
        if LAUNCHER_RUN_ADMIN_BOT:
            logger.debug("Ajout du bot admin aux tâches")
            tasks.append(run_with_shutdown(run_admin_bot(), "Admin Bot"))
        
        if LAUNCHER_RUN_LOGGER_BOT:
            logger.debug("Ajout du bot logger aux tâches")
            tasks.append(run_with_shutdown(run_logger_bot(), "Logger Bot"))
        
        if LAUNCHER_RUN_SECONDARY_BOTS:
            logger.debug("Ajout des bots secondaires aux tâches")
            secondary_bots = [
                (run_mistral_bot(), "Mistral Bot"),
                (run_gemini_bot(), "Gemini Bot"),
                (run_evilgpt_bot(), "EvilGPT Bot"),
                (run_llama_bot(), "Llama Bot"),
                (run_chatgpt_bot(), "ChatGPT Bot"),
                (run_deepseek_bot(), "DeepSeek Bot"),
                (run_grok_bot(), "Grok Bot"),
                (run_perplexity_bot(), "Perplexity Bot"),
                (run_qwen_bot(), "Qwen Bot"),
                (run_claude_bot(), "Claude Bot"),
                (run_phi_bot(), "Phi Bot"),
                (run_kimi_bot(), "Kimi Bot"),
                (run_glm_bot(), "GLM Bot"),
                (run_command_bot(), "Command Bot"),
            ]
            for bot_coro, bot_name in secondary_bots:
                logger.debug(f"Ajout de {bot_name} aux tâches")
                tasks.append(run_with_shutdown(bot_coro, bot_name))
            logger.debug(f"Total de bots secondaires ajoutés: {len(secondary_bots)}")
        
        logger.debug(f"Total de tâches à lancer: {len(tasks)}")
        logger.debug("Démarrage de toutes les tâches avec asyncio.gather()")
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.debug("asyncio.gather() complété")

    except (SystemExit, KeyboardInterrupt):
        logger.info("Arrêt complet du programme.")
        logger.debug("SystemExit ou KeyboardInterrupt reçu")
    except Exception as e:
        logger.error(f"Erreur non gérée : {str(e)}")
        logger.debug(f"Stack trace complet: ", exc_info=True)
    finally:
        logger.debug("Entrée dans le bloc finally de main()")
        
        logger.info("Arrêt du monitoring des ressources...")
        try:
            monitor = get_default_monitor()
            stop_monitoring()
            stop_exporter()
            
            csv_file = f"resource_monitoring_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            monitor.export_to_csv(csv_file)
            logger.info(f"✓ Données de monitoring exportées: {csv_file}")
            
            monitor.print_summary()
        except Exception as e:
            logger.warning(f"Erreur lors de l'arrêt du monitoring: {e}")
        
        pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        logger.debug(f"Nombre de tâches en attente: {len(pending)}")
        if pending:
            logger.debug(f"Détails des tâches en attente: {[t.get_name() for t in pending]}")
            for task in pending:
                logger.debug(f"Annulation de la tâche: {task.get_name()}")
                task.cancel()
            try:
                logger.debug("Attente de la fin des tâches annulées...")
                await asyncio.gather(*pending, return_exceptions=True)
                logger.debug("Toutes les tâches ont été annulées et attendues.")
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage des tâches: {str(e)}")
                logger.debug("Stack trace du nettoyage: ", exc_info=True)
        logger.info("Nettoyage terminé.")

if __name__ == "__main__":
    logger.debug("Démarrage du script principal")
    
    logger.info("=" * 60)
    logger.info("Configuration de démarrage (depuis config.toml):")
    logger.info(f"  API: {'✓' if LAUNCHER_RUN_API else '✗'}")
    logger.info(f"  Bot Principal: {'✓' if LAUNCHER_RUN_MAIN_BOT else '✗'}")
    logger.info(f"  Bots Secondaires: {'✓' if LAUNCHER_RUN_SECONDARY_BOTS else '✗'}")
    logger.info(f"  Bot Admin: {'✓' if LAUNCHER_RUN_ADMIN_BOT else '✗'}")
    logger.info(f"  Bot Logger: {'✓' if LAUNCHER_RUN_LOGGER_BOT else '✗'}")
    logger.info("=" * 60)
    
    logger.debug("Vérification du fichier stop.json...")
    command = check_restart_command()
    logger.debug(f"Commande trouvée dans stop.json: {command}")
    
    if command == "STOP":
        logger.info("Arrêt demandé via stop.json. Le bot ne démarrera pas.")
        logger.debug("Suppression du fichier stop.json...")
        try:
            os.remove("stop.json")
            logger.debug("stop.json supprimé avec succès")
        except Exception:
            logger.debug("Fichier stop.json n'existe pas ou impossible à supprimer")
            pass
        logger.debug("Sortie avec code 0")
        sys.exit(0)
    
    try:
        logger.debug("Suppression du fichier stop.json s'il existe...")
        if os.path.exists("stop.json"):
            os.remove("stop.json")
            logger.debug("stop.json supprimé")
    except Exception as e:
        logger.warning(f"Impossible de supprimer stop.json: {e}")
        logger.debug(f"Exception lors de la suppression de stop.json: {e}", exc_info=True)
    
    try:
        logger.debug("Lancement de asyncio.run(main())...")
        asyncio.run(main())
        logger.debug("asyncio.run(main()) terminé normalement.")
    except KeyboardInterrupt:
        logger.debug("Interruption manuelle - Arrêt du programme.")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        logger.debug(f"Stack trace de l'erreur fatale: {e}", exc_info=True)
        sys.exit(1)
    
    logger.debug(f"Vérification du redémarrage: restart_requested = {restart_requested}")
    if restart_requested:
        logger.info("Redémarrage demandé. Relance du processus...")
        logger.debug("Suppression du fichier stop.json avant redémarrage...")
        try:
            os.remove("stop.json")
            logger.debug("stop.json supprimé avant redémarrage")
        except Exception:
            logger.debug("Fichier stop.json n'existe pas ou impossible à supprimer avant redémarrage")
            pass
        logger.debug(f"Exécution de os.execv({sys.executable}, {[sys.executable] + sys.argv})")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    logger.info("Arrêt complet du bot.")
    logger.debug("Script principal terminé")
