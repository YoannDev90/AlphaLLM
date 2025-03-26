import sqlite3
import logging

logger = logging.getLogger("AlphaLLM")

DATABASE_PATH = "config/alphallm.db"

def initialize_roles():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            guild_id INTEGER,
            model TEXT,
            role_id INTEGER
        )
    """)
    conn.commit()
    logger.info("Database initialisée !")
    conn.close()

def initialize_langs():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER,
            default_model TEXT,
            lang TEXT,
            nb_queries INTEGER,
            nb_images INTEGER
        )
    """)
    conn.commit()
    logger.info("Database initialisée !")
    conn.close()