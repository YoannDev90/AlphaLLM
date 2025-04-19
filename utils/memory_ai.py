import os
import asyncpg
import logging
from fastembed import TextEmbedding
from typing import List, Dict, Optional

logger = logging.getLogger('AlphaLLM')

_PG_POOL: Optional[asyncpg.pool.Pool] = None
_EMBEDDER: Optional[TextEmbedding] = None

async def connect_to_db() -> None:
    """Établit la connexion à la base de données"""
    global _PG_POOL
    try:
        _PG_POOL = await asyncpg.create_pool(
            dsn=os.getenv("DB_DIRECT_CONN"),
            min_size=2,
            max_size=10,
            ssl='require'
        )
        logger.debug("🟢 Connexion réussie à Supabase")
    except Exception as e:
        logger.critical(f"🔴 Échec de connexion: {str(e)}")
        raise

def initialize_embedder(model_name: str = "BAAI/bge-small-en-v1.5") -> None:
    """Initialise le modèle d'embedding"""
    global _EMBEDDER
    try:
        _EMBEDDER = TextEmbedding(model_name)
        logger.debug(f"🦾 Modèle d'embedding initialisé ({model_name})")
    except Exception as e:
        logger.error(f"🔴 Erreur d'initialisation du modèle: {str(e)}")
        raise

async def init_db() -> None:
    """Initialise les structures de la base de données"""
    async with _PG_POOL.acquire() as conn:
        try:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding vector(384),
                    user_id TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS user_idx 
                ON memories USING HASH (user_id)
            ''')
            logger.debug("🏗️  Base de données initialisée")
        except Exception as e:
            logger.error(f"🔴 Erreur d'initialisation: {str(e)}")
            raise

async def add_memory(user_id: str, text: str) -> None:
    """Ajoute une entrée en mémoire avec embedding"""
    logger.debug(f"Tentative d'ajout mémoire pour {user_id}")
    
    try:
        embedding = _generate_embedding(text)
        vec_str = _vec_to_str(embedding)
        
        async with _PG_POOL.acquire() as conn:
            await conn.execute('''
                INSERT INTO memories (content, embedding, user_id)
                VALUES ($1, $2::vector, $3)
            ''', text, vec_str, user_id)
            
        logger.info(f"🧠 Nouvelle mémoire stockée pour {user_id} (longueur: {len(text)} caractères)")

    except Exception as e:
        logger.error(f"🔴 Erreur d'ajout: {str(e)}")
        raise

async def get_history(user_id: str, limit: int = 100) -> List[Dict]:
    """Récupère l'historique d'un utilisateur"""
    logger.debug(f"Récupération historique pour {user_id}")
    
    try:
        async with _PG_POOL.acquire() as conn:
            records = await conn.fetch('''
                SELECT content, created_at 
                FROM memories 
                WHERE user_id = $1 
                ORDER BY created_at DESC
                LIMIT $2
            ''', user_id, limit)
            
            logger.info(f"📜 Historique récupéré: {len(records)} entrées")
            return [dict(r) for r in records]
            
    except Exception as e:
        logger.error(f"🔴 Erreur de récupération: {str(e)}")
        return []

async def clear_history(user_id: str) -> None:
    """Supprime toutes les données d'un utilisateur"""
    logger.warning(f"Demande de suppression historique pour {user_id}")
    
    try:
        async with _PG_POOL.acquire() as conn:
            await conn.execute('DELETE FROM memories WHERE user_id = $1', user_id)
            
        logger.info(f"🧹 Historique supprimé pour {user_id}")
        
    except Exception as e:
        logger.error(f"🔴 Erreur de suppression: {str(e)}")
        raise

def _generate_embedding(text: str) -> List[float]:
    """Génère les embeddings de texte"""
    if not _EMBEDDER:
        raise ValueError("Embedder non initialisé")
    
    try:
        return list(_EMBEDDER.embed([text]))[0].tolist()
    except Exception as e:
        logger.error(f"🔴 Erreur d'embedding: {str(e)}")
        raise

def _vec_to_str(vec: List[float]) -> str:
    """Convertit un vecteur en chaîne pour PostgreSQL"""
    return '[' + ','.join(f"{x:.8f}" for x in vec) + ']'

async def initialize():
    """Initialisation globale"""
    await connect_to_db()
    initialize_embedder()
    await init_db()
