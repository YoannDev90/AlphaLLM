import os
import asyncpg
import logging
import hashlib
import time
from fastembed import TextEmbedding
from typing import List, Dict, Optional

logger = logging.getLogger('AlphaLLM')

_PG_POOL: Optional[asyncpg.pool.Pool] = None
_EMBEDDER: Optional[TextEmbedding] = None

async def connect_to_db() -> None:
    global _PG_POOL
    try:
        _PG_POOL = await asyncpg.create_pool(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            ssl='require'
        )
        logger.debug("🟢 Connexion réussie à Supabase (mode paramètres)")
    except Exception as e:
        logger.critical(f"🔴 Échec de connexion: {str(e)}")
        raise


def initialize_embedder(model_name: str = "BAAI/bge-small-en-v1.5") -> None:
    global _EMBEDDER
    try:
        _EMBEDDER = TextEmbedding(model_name)
        logger.debug(f"🦾 Modèle d'embedding initialisé ({model_name})")
    except Exception as e:
        logger.error(f"🔴 Erreur d'initialisation du modèle: {str(e)}")
        raise

async def init_db() -> None:
    async with _PG_POOL.acquire() as conn:
        try:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    embedding vector(384),
                    user_id BIGINT,
                    server_id BIGINT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS user_server_idx 
                ON memories (user_id, server_id)
            ''')
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS created_at_idx
                ON memories (created_at)
            ''')
            logger.debug("🏗️  Base de données initialisée")
        except Exception as e:
            logger.error(f"🔴 Erreur d'initialisation: {str(e)}")
            raise

async def _delete_old_memories() -> None:
    """Supprime les mémoires de plus d'1h"""
    async with _PG_POOL.acquire() as conn:
        try:
            await conn.execute('''
                DELETE FROM memories WHERE created_at < NOW() - INTERVAL '12 hour'
            ''')
            logger.debug("🧹 Mémoires de plus d'1h supprimées")
        except Exception as e:
            logger.error(f"🔴 Erreur lors du nettoyage: {str(e)}")

def _generate_id(user_id: int, server_id: int) -> str:
    """Génère un ID unique basé sur user, serveur et timestamp"""
    base = f"{user_id}:{server_id}:{time.time_ns()}"
    return hashlib.sha256(base.encode()).hexdigest()

async def add_memory(user_id: int, server_id: int, text: str) -> None:
    logger.debug(f"Tentative d'ajout mémoire pour {user_id} sur {server_id}")
    await _delete_old_memories()
    try:
        embedding = _generate_embedding(text)
        vec_str = _vec_to_str(embedding)
        entry_id = _generate_id(user_id, server_id)
        async with _PG_POOL.acquire() as conn:
            await conn.execute('''
                INSERT INTO memories (id, content, embedding, user_id, server_id)
                VALUES ($1, $2, $3::vector, $4, $5)
            ''', entry_id, text, vec_str, user_id, server_id)
        logger.debug(f"🧠 Nouvelle mémoire stockée pour {user_id} sur {server_id} (longueur: {len(text)} caractères)")
    except Exception as e:
        logger.error(f"🔴 Erreur d'ajout: {str(e)}")
        raise

async def get_history(user_id: int, server_id: int, limit: int = 100) -> List[Dict]:
    logger.debug(f"Récupération historique pour {user_id} sur {server_id}")
    await _delete_old_memories()
    try:
        async with _PG_POOL.acquire() as conn:
            records = await conn.fetch('''
                SELECT id, content, created_at 
                FROM memories 
                WHERE user_id = $1 AND server_id = $2
                ORDER BY created_at DESC
                LIMIT $3
            ''', user_id, server_id, limit)
            logger.debug(f"📜 Historique récupéré: {len(records)} entrées")
            return [dict(r) for r in records]
    except Exception as e:
        logger.error(f"🔴 Erreur de récupération: {str(e)}")
        return []

async def clear_history(user_id: int, server_id: int) -> None:
    logger.warning(f"Demande de suppression historique pour {user_id} sur {server_id}")
    try:
        async with _PG_POOL.acquire() as conn:
            await conn.execute('DELETE FROM memories WHERE user_id = $1 AND server_id = $2', user_id, server_id)
        logger.info(f"🧹 Historique supprimé pour {user_id} sur {server_id}")
    except Exception as e:
        logger.error(f"🔴 Erreur de suppression: {str(e)}")
        raise

def _generate_embedding(text: str) -> List[float]:
    if not _EMBEDDER:
        raise ValueError("Embedder non initialisé")
    try:
        return list(_EMBEDDER.embed([text]))[0].tolist()
    except Exception as e:
        logger.error(f"🔴 Erreur d'embedding: {str(e)}")
        raise

def _vec_to_str(vec: List[float]) -> str:
    return '[' + ','.join(f"{x:.8f}" for x in vec) + ']'

async def initialize() -> None:
    await connect_to_db()
    initialize_embedder()
    await init_db()
