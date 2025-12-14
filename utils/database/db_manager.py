import asyncio
import json
import logging
import re
import sqlite3
from datetime import datetime

import psycopg2

from config import (LOGGER_NAME, SUPABASE_PG, TABLES_TO_CLONE, SUPABASE_PASSWORD)

logger = logging.getLogger(LOGGER_NAME)

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.sqlite_conn = None
            self.pg_conn = None
            self.initialized = True

    async def initialize(self):
        """Initialise les connexions aux bases de données"""
        try:
            self.sqlite_conn = sqlite3.connect("local_db.db")
            logger.debug("Connexion SQLite établie avec succès")
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la connexion à la base de données SQLite: {e}")
            raise

        try:
            self.pg_conn = psycopg2.connect(SUPABASE_PG)
            logger.debug("Connexion PostgreSQL établie avec succès")
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la connexion à PostgreSQL: {e}")
            raise

    async def clone_tables(self):
        """Clone les tables spécifiées de Supabase vers SQLite"""
        if not self.pg_conn or not self.sqlite_conn:
            await self.initialize()

        for table_name in TABLES_TO_CLONE:
            try:
                logger.debug(f"Clonage de la table {table_name}")
                
                with self.pg_conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' AND table_name = %s 
                        ORDER BY ordinal_position
                    """, (table_name,))
                    columns = [row[0] for row in cursor.fetchall()]
                
                if not columns:
                    logger.warning(f"Aucune colonne trouvée pour la table {table_name}")
                    continue
                
                with self.pg_conn.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                
                data = [dict(zip(columns, row)) for row in rows]
                
                if data:
                    column_defs = ", ".join([f"{col} TEXT" for col in columns])

                    self.sqlite_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                    self.sqlite_conn.execute(f"CREATE TABLE {table_name} ({column_defs})")
                    placeholders = ", ".join(["?" for _ in columns])
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    for row in data:
                        values = [json.dumps(row[col]) if isinstance(row[col], (list, dict)) else row[col] for col in columns]
                        self.sqlite_conn.execute(insert_sql, values)
                    self.sqlite_conn.commit()
                    logger.debug(f"Table {table_name} clonée avec succès ({len(data)} lignes)")
                else:
                    logger.debug(f"Table {table_name} vide, création de table vide")
                    column_defs = ", ".join([f"{col} TEXT" for col in columns])
                    self.sqlite_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                    self.sqlite_conn.execute(f"CREATE TABLE {table_name} ({column_defs})")
                    self.sqlite_conn.commit()
            except Exception as e:
                logger.error(f"Erreur lors du clonage de {table_name}: {e}")

    async def exc_get_query(self, query: str, params: tuple = ()):
        """Exécute une requête SELECT dans la base de données SQLite et retourne les résultats"""
        try:
            if self.sqlite_conn is None:
                logger.error("sqlite_conn is None in exc_get_query")
                return []
            cursor = self.sqlite_conn.execute(query, params)
            rows = cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de l'exécution de la requête: {e}")
            return []
        
    async def exc_modify_query(self, query: str, params: tuple = ()):
        """Exécute une requête INSERT/UPDATE/DELETE dans SQLite et synchronise avec Supabase"""
        try:
            if self.sqlite_conn is None:
                logger.error("sqlite_conn is None in exc_modify_query")
                return 0
            cursor = self.sqlite_conn.execute(query, params)
            self.sqlite_conn.commit()
            
            await self._sync_with_supabase(query, params)
            
            return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de l'exécution de la requête SQLite: {e}")
            return 0
    
    async def _sync_with_supabase(self, query: str, params: tuple):
        """Convertit la requête SQLite en PostgreSQL et l'exécute sur Supabase"""
        try:
            pg_query = self._convert_sqlite_to_postgres(query)
            logger.debug(f"Executing PG query: {pg_query} with params: {params}")
            with self.pg_conn.cursor() as cursor:
                cursor.execute(pg_query, params)
                self.pg_conn.commit()
            logger.debug(f"Synchronisation réussie: {pg_query}")
        except psycopg2.Error as e:
            logger.warning(f"Échec de synchronisation PostgreSQL: {e}")
    
    def _convert_sqlite_to_postgres(self, sqlite_query: str) -> str:
        """Convertit une requête SQLite en PostgreSQL (remplace ? par %s)"""
        pg_query = sqlite_query.replace('?', '%s')
        logger.debug(f"Converted query: {sqlite_query} -> {pg_query}")
        return pg_query