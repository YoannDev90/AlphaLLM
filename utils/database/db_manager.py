from supabase import create_client, Client, ClientOptions
from datetime import datetime
import logging
import sqlite3
import asyncio
import json

from config import SUPABASE_URL, SUPABASE_KEY, JWT_KEY

logger = logging.getLogger("AlphaLLM")

# Liste des tables à cloner
TABLES_TO_CLONE = ["blacklist", "server_settings", "users_settings", "users"]

class DatabaseManager:
    def __init__(self):
        self.supabase_client = None
        self.sqlite_conn = None

    async def initialize(self):
        """Initialise les connexions aux bases de données"""
        try:
            self.supabase_client = create_client(
                SUPABASE_URL,
                SUPABASE_KEY,
                options=ClientOptions(
                    schema="public",
                    headers={"Authorization": f"Bearer {JWT_KEY}"},
                    auto_refresh_token=True,
                    persist_session=True
                )
            )
            logger.debug("Client Supabase initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client Supabase: {e}")
            raise

        try:
            self.sqlite_conn = sqlite3.connect("local_db.db")
            logger.debug("Connexion SQLite établie avec succès")
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la connexion à la base de données SQLite: {e}")
            raise

    async def clone_tables(self):
        """Clone les tables spécifiées de Supabase vers SQLite"""
        if not self.supabase_client or not self.sqlite_conn:
            await self.initialize()

        for table_name in TABLES_TO_CLONE:
            try:
                logger.info(f"Clonage de la table {table_name}")
                # Récupérer les données de Supabase
                response = self.supabase_client.table(table_name).select("*").execute()
                data = response.data

                if data:
                    # Inférer le schéma à partir des données
                    columns = list(data[0].keys())
                    column_defs = ", ".join([f"{col} TEXT" for col in columns])  # Simplifié, tout en TEXT

                    # Supprimer la table si elle existe
                    self.sqlite_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                    # Créer la table
                    self.sqlite_conn.execute(f"CREATE TABLE {table_name} ({column_defs})")
                    # Insérer les données
                    placeholders = ", ".join(["?" for _ in columns])
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    for row in data:
                        values = [json.dumps(row[col]) if isinstance(row[col], (list, dict)) else row[col] for col in columns]
                        self.sqlite_conn.execute(insert_sql, values)
                    self.sqlite_conn.commit()
                    logger.info(f"Table {table_name} clonée avec succès ({len(data)} lignes)")
                else:
                    logger.info(f"Table {table_name} vide, création de table vide")
                    # Créer table vide si nécessaire, mais pour l'instant skip
            except Exception as e:
                logger.error(f"Erreur lors du clonage de {table_name}: {e}")

    # Getters - lisent depuis SQLite
    async def get_blacklist(self):
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT * FROM blacklist")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste noire : {str(e)}")
            return None

    async def get_allowed_channels(self, guild_id):
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT forbidden_channels FROM server_settings WHERE id_discord = ?", (guild_id,))
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    return json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    return row[0]
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des canaux autorisés : {str(e)}")
            return None

    async def get_allowed_roles(self, guild_id):
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT forbidden_roles FROM server_settings WHERE id_discord = ?", (guild_id,))
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    return json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    return row[0]
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des rôles autorisés : {str(e)}")
            return None

    # Setters - modifient SQLite et Supabase
    async def blacklist_add(self, user_id: int, reason: str):
        try:
            data = {
                "id_discord": user_id,
                "reason": reason,
                "datetime": datetime.now().isoformat()
            }
            # Insérer dans Supabase
            response = self.supabase_client.table("blacklist").insert(data).execute()
            # Insérer dans SQLite
            cursor = self.sqlite_conn.cursor()
            cursor.execute("INSERT INTO blacklist (id_discord, reason, datetime) VALUES (?, ?, ?)",
                           (user_id, reason, data["datetime"]))
            self.sqlite_conn.commit()
            return response.data
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout à la liste noire : {str(e)}")
            return None

    async def blacklist_remove(self, user_id: int):
        try:
            # Supprimer de Supabase
            response = self.supabase_client.table("blacklist").delete().eq("id_discord", user_id).execute()
            # Supprimer de SQLite
            cursor = self.sqlite_conn.cursor()
            cursor.execute("DELETE FROM blacklist WHERE id_discord = ?", (user_id,))
            self.sqlite_conn.commit()
            return response.data
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la liste noire : {str(e)}")
            return None

    # Méthodes pour users_settings et server_settings
    async def update_user_settings(self, user_id: int, settings: dict):
        try:
            # Upsert dans Supabase
            response = self.supabase_client.table("users_settings").upsert({"id_discord": user_id, **settings}).execute()
            # Upsert dans SQLite (simplifié, suppose que la table a les colonnes)
            cursor = self.sqlite_conn.cursor()
            columns = list(settings.keys()) + ["id_discord"]
            values = [json.dumps(v) if isinstance(v, (list, dict)) else v for v in settings.values()] + [user_id]
            placeholders = ", ".join(["?" for _ in values])
            upsert_sql = f"INSERT OR REPLACE INTO users_settings ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(upsert_sql, values)
            self.sqlite_conn.commit()
            return response.data
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des paramètres utilisateur : {str(e)}")
            return None

    async def update_server_settings(self, guild_id: int, settings: dict):
        try:
            # Upsert dans Supabase
            response = self.supabase_client.table("server_settings").upsert({"id_discord": guild_id, **settings}).execute()
            # Upsert dans SQLite
            cursor = self.sqlite_conn.cursor()
            columns = list(settings.keys()) + ["id_discord"]
            values = [json.dumps(v) if isinstance(v, (list, dict)) else v for v in settings.values()] + [guild_id]
            placeholders = ", ".join(["?" for _ in values])
            upsert_sql = f"INSERT OR REPLACE INTO server_settings ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(upsert_sql, values)
            self.sqlite_conn.commit()
            return response.data
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des paramètres serveur : {str(e)}")
            return None

# Instance globale
db_manager = DatabaseManager()

# Fonctions pour compatibilité
def get_supabase_client() -> Client:
    return db_manager.supabase_client

def get_sqlite_connection(db_path: str = "local_db.db") -> sqlite3.Connection:
    return db_manager.sqlite_conn
    