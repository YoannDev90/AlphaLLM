"""
main.py

This module serves as the entry point for the application. It initializes the
necessary components, such as roles and languages, and runs the main bot and
logger bot concurrently.
"""

import asyncio
from bot import run_bot
from logger_bot import run_logger_bot
from utils.langs import load_language

async def main():
    """
    Main function to initialize roles, languages, and run the bots concurrently.
    """
    load_language("en")
    await asyncio.gather(run_bot(), run_logger_bot())

if __name__ == "__main__":
    asyncio.run(main())
