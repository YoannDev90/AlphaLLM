#utils/roles_utils.py

import discord
import sqlite3
import logging
from utils.langs import get_translation

logger = logging.getLogger("AlphaLLM")

DATABASE_PATH = "config/alphallm.db"

def initialize_database():
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

def save_role_to_db(guild_id, model, role_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO roles (guild_id, model, role_id) VALUES (?, ?, ?)", (guild_id, model, role_id))
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du rôle {role_id} pour le modèle {model} : {e}")
    finally:
        conn.commit()
        conn.close()

def remove_role_from_db(role_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM roles WHERE role_id = ?", (role_id,))
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du rôle {role_id} : {e}")
    finally:
        conn.commit()
        conn.close()

def get_role_from_db(guild_id, model):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT role_id FROM roles WHERE guild_id = ? AND model = ?", (guild_id, model))
        result = cursor.fetchone()
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du rôle pour le modèle {model} : {e}")
    finally:
        conn.close()
    return result

async def create_role(guild, role_name, color=discord.Color.default(), mentionable=True):
    try:
        role = await guild.create_role(name=role_name, color=color, mentionable=mentionable)
        return role
    except Exception as e:
        logger.error(f"Erreur lors de la création du rôle {role_name} : {e}")
        return None

async def assign_role_to_bot(bot_member, role):
    try:
        await bot_member.add_roles(role)
    except Exception as e:
        logger.error(f"Erreur lors de l'attribution du rôle {role.name} au bot : {e}")

async def remove_role_from_bot(bot_member, role):
    try:
        await bot_member.remove_roles(role)
        remove_role_from_db(role.id)
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du rôle {role.name} du bot : {e}")

async def delete_role(role):
    try:
        await role.delete()
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du rôle {role.name} : {e}")
