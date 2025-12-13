import asyncio
import datetime
import logging
import signal

from api.api import start_api_async
from bots.admin_bot import run_admin_bot
from bots.bot import bot, run_bot
from bots.logger_bot import run_logger_bot
from config import LOGGER_NAME
from logger import close_logging, setup_logging
from utils.memory import initialize_memory_manager
from utils.ressources import start_monitoring, stop_monitoring

shutdown_event = asyncio.Event()

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
    setup_logging(bot)
    logger = logging.getLogger(LOGGER_NAME)
    logger.info(f"Booting {LOGGER_NAME}")
    
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    
    try:
        csv_file = "resource_monitoring.csv"        
        logger.info("Démarrage du monitoring des ressources...")
        monitor = start_monitoring(interval=1, csv_file=csv_file)
        
        monitor.fill_gaps(datetime.datetime.now())
        await initialize_memory_manager()
        
        tasks = [
            run_with_shutdown(run_logger_bot(), "Logger Bot"),
            run_with_shutdown(run_bot(bot), "Bot principal"),
            run_with_shutdown(run_admin_bot(), "Admin Bot"),
            run_with_shutdown(start_api_async(), "API Server"),
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

if __name__ == "__main__":
    asyncio.run(main())
