#main.py

import asyncio
from bot import run_bot
from logger_bot import run_logger_bot
from utils.roles_utils import initialize_database
from utils.langs import load_language

async def main():
    initialize_database()
    load_language("fr")
    await asyncio.gather(run_bot(), run_logger_bot())
    #await asyncio.gather(run_bot())


if __name__ == "__main__":
    asyncio.run(main())
