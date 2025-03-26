"""
roles_utils.py

This module provides utility functions for managing Discord roles and their
interaction with a SQLite database. It includes functions to create, assign,
remove, and delete roles, as well as database operations for storing and
retrieving role information.
"""

import discord
import sqlite3
import logging
from utils.langs import get_translation

logger = logging.getLogger("AlphaLLM")

DATABASE_PATH = "config/alphallm.db"

def save_role_to_db(guild_id, model, role_id):
    """
    Save a role to the database.

    Args:
        guild_id (int): The ID of the Discord guild.
        model (str): The name of the model associated with the role.
        role_id (int): The ID of the Discord role.
    """
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
    """
    Remove a role from the database.

    Args:
        role_id (int): The ID of the Discord role to remove.
    """
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
    """
    Retrieve a role ID from the database based on guild ID and model.

    Args:
        guild_id (int): The ID of the Discord guild.
        model (str): The name of the model associated with the role.

    Returns:
        tuple: A tuple containing the role ID, or None if not found.
    """
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
    """
    Create a new role in a Discord guild.

    Args:
        guild (discord.Guild): The Discord guild where the role will be created.
        role_name (str): The name of the role.
        color (discord.Color, optional): The color of the role. Defaults to default color.
        mentionable (bool, optional): Whether the role is mentionable. Defaults to True.

    Returns:
        discord.Role: The created role, or None if an error occurred.
    """
    try:
        role = await guild.create_role(name=role_name, color=color, mentionable=mentionable)
        return role
    except Exception as e:
        logger.error(f"Erreur lors de la création du rôle {role_name} : {e}")
        return None

async def assign_role_to_bot(bot_member, role):
    """
    Assign a role to the bot.

    Args:
        bot_member (discord.Member): The bot's member object.
        role (discord.Role): The role to assign.
    """
    try:
        await bot_member.add_roles(role)
    except Exception as e:
        logger.error(f"Erreur lors de l'attribution du rôle {role.name} au bot : {e}")

async def remove_role_from_bot(bot_member, role):
    """
    Remove a role from the bot and delete it from the database.

    Args:
        bot_member (discord.Member): The bot's member object.
        role (discord.Role): The role to remove.
    """
    try:
        await bot_member.remove_roles(role)
        remove_role_from_db(role.id)
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du rôle {role.name} du bot : {e}")

async def delete_role(role):
    """
    Delete a role from a Discord guild.

    Args:
        role (discord.Role): The role to delete.
    """
    try:
        await role.delete()
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du rôle {role.name} : {e}")
