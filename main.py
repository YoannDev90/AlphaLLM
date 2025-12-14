import asyncio
import datetime
import json
import logging
import os
import signal

from api.api import start_api_async
from bots.admin_bot import create_admin_bot, run_admin_bot
from bots.bot import create_bot, run_bot
from bots.logger_bot import create_logger_bot, run_logger_bot
from config import LOGGER_NAME
from logger import close_logging, setup_logging
from utils.database.db_manager import DatabaseManager
from utils.memory import initialize_memory_manager
from utils.ressources import get_default_monitor, start_monitoring, stop_monitoring
import utils.ressources as ressources

shutdown_event = asyncio.Event()
db_manager = DatabaseManager()

shutdown_event = asyncio.Event()
db_manager = DatabaseManager()

async def check_stop_file(restart_pending):
    """Vérifie périodiquement la présence du fichier stop.json"""
    logger = logging.getLogger(LOGGER_NAME)
    while not shutdown_event.is_set():
        if os.path.exists("stop.json"):
            try:
                with open("stop.json", "r") as f:
                    data = json.load(f)
                command = data.get("COMMAND")
                if command == "STOP":
                    logger.info("Commande STOP détectée, arrêt en cours...")
                    shutdown_event.set()
                elif command == "RESTART":
                    logger.info("Commande RESTART détectée, redémarrage en cours...")
                    shutdown_event.set()
                    restart_pending[0] = True
                os.remove("stop.json")
                break
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du fichier stop.json: {e}")
        await asyncio.sleep(1)

def handle_shutdown_signal(signum, frame):
    """Gestionnaire de signal pour arrêt propre"""
    logger = logging.getLogger(LOGGER_NAME)
    logger.debug(f"Signal {signum} reçu, arrêt en cours...")
    shutdown_event.set()

async def run_with_shutdown(coro, name="task"):
    """Execute une coroutine et l'annule quand shutdown_event est set"""
    logger = logging.getLogger(LOGGER_NAME)
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

async def main() -> None:
    if os.path.exists("stop.json"):
        try:
            with open("stop.json", "r") as f:
                data = json.load(f)
            command = data.get("COMMAND")
            if command == "STOP":
                os.remove("stop.json")
                return
            elif command == "RESTART":
                os.remove("stop.json")
        except Exception as e:
            logger = logging.getLogger(LOGGER_NAME)
            logger.error(f"Erreur lors de la lecture du fichier stop.json au démarrage: {e}")
    
    restart_pending = [False]
    while True:
        shutdown_event.clear()
        
        bot = create_bot()
        admin_bot = create_admin_bot()
        logger_bot = create_logger_bot()
        
        setup_logging(bot)
        logger = logging.getLogger(LOGGER_NAME)
        logger.info(f"Booting {LOGGER_NAME}")
        
        signal.signal(signal.SIGTERM, handle_shutdown_signal)
        signal.signal(signal.SIGINT, handle_shutdown_signal)
        
        try:
            ressources._monitor_instance = None
            
            csv_file = "monitoring.csv"        
            logger.info("Démarrage du monitoring des ressources...")
            monitor = start_monitoring(interval=1, csv_file=csv_file)
            
            monitor.fill_gaps(datetime.datetime.now())
            await initialize_memory_manager()
            
            logger.info("Initialisation de la base de données...")
            await db_manager.initialize()
            await db_manager.clone_tables()
            
            tasks = [
                run_with_shutdown(run_logger_bot(logger_bot), "Logger Bot"),
                run_with_shutdown(run_bot(bot), "Main Bot"),
                run_with_shutdown(run_admin_bot(admin_bot), "Admin Bot"),
                run_with_shutdown(start_api_async(), "API Server"),
                run_with_shutdown(check_stop_file(restart_pending), "Stop-File Checker"),
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except (SystemExit, KeyboardInterrupt):
            logger.info("Arrêt complet du programme.")
        finally:        
            try:
                stop_monitoring()
                close_logging()
            except Exception as e:
                logger.warning(f"Erreur lors de l'arrêt du monitoring: {e}")
        
        break

if __name__ == "__main__":
    asyncio.run(main())
