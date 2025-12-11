import asyncio
import logging
import signal
import os
import json
import datetime

from bots.bot import bot, run_bot
from bots.admin_bot import run_admin_bot
from bots.logger_bot import run_logger_bot

from api.api import start_api_async

from logger import setup_logging
from config import LOGGER_NAME
from utils.ressources import start_monitoring, stop_monitoring, get_default_monitor
from utils.memory import initialize_memory_manager

shutdown_event = asyncio.Event()

def handle_shutdown_signal(signum, frame):
    """Gestionnaire de signal pour arrêt propre"""
    logger = logging.getLogger(LOGGER_NAME)
    logger.debug(f"Signal {signum} reçu, arrêt en cours...")
    shutdown_event.set()

async def log_resource_usage():
    """Enregistre périodiquement l'utilisation des ressources"""
    logger = logging.getLogger(LOGGER_NAME)
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
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des ressources: {e}")
        
        if shutdown_event.is_set():
            break

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
        monitor = start_monitoring(interval=0.5, csv_file=csv_file)
        
        # Fill gaps if CSV exists
        monitor.fill_gaps(datetime.datetime.now())
        await initialize_memory_manager()
        
        tasks = [
            run_with_shutdown(log_resource_usage(), "Resource Logger"),
            run_with_shutdown(run_logger_bot(), "Logger Bot"),
            run_with_shutdown(run_bot(bot), "Bot principal"),
            run_with_shutdown(run_admin_bot(), "Admin Bot"),
            run_with_shutdown(start_api_async(), "API Server"),
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
    except (SystemExit, KeyboardInterrupt):
        logger.info("Arrêt complet du programme.")
    finally:        
        logger.info("Arrêt du monitoring des ressources...")
        try:
            stop_monitoring()
            monitor.print_summary()
        except Exception as e:
            logger.warning(f"Erreur lors de l'arrêt du monitoring: {e}")

if __name__ == "__main__":
    asyncio.run(main())
