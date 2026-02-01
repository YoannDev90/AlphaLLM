import asyncio
import datetime
import json
import logging
import os
import signal
from pathlib import Path

import utils.ressources as ressources
from api.api import start_api_async
from bots.admin_bot import run_admin_bot
from bots.bot import run_bot
from bots.logger_bot import run_logger_bot
from bots.sec_bots import run_addon_bots
from config import LOGGER_NAME
from logger import close_logging, setup_logging
from utils.database.db_manager import DatabaseManager
from utils.discord_utils.status import status_emulation
from utils.function_calling import initialize_function_caller
from utils.memory import initialize_memory_manager
from utils.ressources import start_monitoring, stop_monitoring

shutdown_event = asyncio.Event()
db_manager = DatabaseManager()

RUN_API = True
RUN_LOGGER_BOT = True
RUN_MAIN_BOT = True
RUN_ADMIN_BOT = True
RUN_SEC_BOTS = True


async def check_stop_file(restart_pending):
    """Vérifie périodiquement la présence du fichier stop.json"""
    logger = logging.getLogger(LOGGER_NAME)
    while not shutdown_event.is_set():
        if Path("stop.json").exists():
            try:
                with open(Path("stop.json"), "r") as f:
                    data = json.load(f)
                command = data.get("COMMAND")
                if command == "STOP":
                    logger.info("Commande STOP détectée, arrêt en cours...")
                    shutdown_event.set()
                elif command == "RESTART":
                    logger.info("Commande RESTART détectée, redémarrage en cours...")
                    shutdown_event.set()
                    restart_pending[0] = True
                os.remove(Path("stop.json"))
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
        return_when=asyncio.FIRST_COMPLETED,
    )

    if task in done:
        logger.info(f"Tâche {name} terminée")
        if task.exception():
            logger.error(f"Tâche {name} a levé une exception: {task.exception()}")
        else:
            logger.info(f"Tâche {name} terminée normalement")

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
    if Path("stop.json").exists():
        try:
            with open(Path("stop.json"), "r") as f:
                data = json.load(f)
            command = data.get("COMMAND")
            if command == "STOP":
                os.remove(Path("stop.json"))
                return
            elif command == "RESTART":
                os.remove(Path("stop.json"))
        except Exception as e:
            logger = logging.getLogger(LOGGER_NAME)
            logger.error(
                f"Erreur lors de la lecture du fichier stop.json au démarrage: {e}"
            )

    restart_pending = [False]
    while True:
        shutdown_event.clear()

        setup_logging()
        logger = logging.getLogger(LOGGER_NAME)
        logger.info(f"Booting {LOGGER_NAME}")

        signal.signal(signal.SIGTERM, handle_shutdown_signal)
        signal.signal(signal.SIGINT, handle_shutdown_signal)

        try:
            ressources._monitor_instance = None

            csv_file = "data/monitoring.csv"
            logger.debug("Démarrage du monitoring des ressources...")
            monitor = start_monitoring(interval=1.0, csv_file=csv_file)

            monitor.fill_gaps(datetime.datetime.now())
            await asyncio.gather(
                initialize_memory_manager(), initialize_function_caller()
            )

            logger.debug("Initialisation de la base de données...")
            await db_manager.initialize()
            await db_manager.clone_tables()

            tasks = [
                (
                    run_with_shutdown(run_logger_bot(), "Logger Bot")
                    if RUN_LOGGER_BOT
                    else asyncio.sleep(0)
                ),
                (
                    run_with_shutdown(run_bot(), "Main Bot")
                    if RUN_MAIN_BOT
                    else asyncio.sleep(0)
                ),
                (
                    run_with_shutdown(run_admin_bot(), "Admin Bot")
                    if RUN_ADMIN_BOT
                    else asyncio.sleep(0)
                ),
                (
                    run_with_shutdown(run_addon_bots(), "Sec Bots")
                    if RUN_SEC_BOTS
                    else asyncio.sleep(0)
                ),
                (
                    run_with_shutdown(start_api_async(), "API Server")
                    if RUN_API
                    else asyncio.sleep(0)
                ),
                run_with_shutdown(
                    check_stop_file(restart_pending), "Stop-File Checker"
                ),
                run_with_shutdown(status_emulation(shutdown_event), "Status Emulation"),
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
