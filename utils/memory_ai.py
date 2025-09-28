import asyncpg
import logging
from utils.config import LOGGER_NAME, EnvVars
import hashlib
import time
import json
from fastembed import TextEmbedding
from typing import List, Dict, Optional

logger = logging.getLogger(LOGGER_NAME)

_PG_POOL: Optional[asyncpg.pool.Pool] = None
_EMBEDDER: Optional[TextEmbedding] = None

async def connect_to_db() -> None:
    global _PG_POOL
    try:
        _PG_POOL = await asyncpg.create_pool(
            host=EnvVars.DB_HOST,
            port=int(EnvVars.DB_PORT),
            user=EnvVars.DB_USER,
            password=EnvVars.DB_PASSWORD,
            database=EnvVars.DB_NAME,
            ssl='require'
        )
    except Exception as e:
        logger.critical(f"Échec de connexion: {str(e)}")
        raise


def initialize_embedder(model_name: str = "BAAI/bge-small-en-v1.5") -> None:
    global _EMBEDDER
    try:
        _EMBEDDER = TextEmbedding(model_name)
    except Exception as e:
        logger.error(f"Erreur d'initialisation du modèle: {str(e)}")
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
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS embedding_idx
                ON memories USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            ''')
        except Exception as e:
            logger.error(f"Erreur d'initialisation: {str(e)}")
            raise

async def _delete_old_memories() -> None:
    """Supprime les mémoires de plus de 8h"""
    async with _PG_POOL.acquire() as conn:
        try:
            await conn.execute('''
                DELETE FROM memories WHERE created_at < NOW() - INTERVAL '8 hour'
            ''')
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {str(e)}")

def _generate_id(user_id: int, server_id: int) -> str:
    """Génère un ID unique basé sur user, serveur et timestamp"""
    base = f"{user_id}:{server_id}:{time.time_ns()}"
    return hashlib.sha256(base.encode()).hexdigest()

async def add_memory(user_id: int, server_id: int, reponse: dict, text_to_embed: str) -> None:
    await _delete_old_memories()
    try:
        embedding = _generate_embedding(text_to_embed)
        vec_str = _vec_to_str(embedding)
        entry_id = _generate_id(user_id, server_id)
        # Sérialise le dictionnaire en JSON pour la colonne jsonb
        content_json = json.dumps(reponse, ensure_ascii=False)
        async with _PG_POOL.acquire() as conn:
            await conn.execute('''
                INSERT INTO memories (id, content, embedding, user_id, server_id)
                VALUES ($1, $2, $3::vector, $4, $5)
            ''', entry_id, content_json, vec_str, user_id, server_id)
    except Exception as e:
        logger.error(f"Erreur d'ajout: {str(e)}")
        raise

async def get_history(user_id: int, server_id: int, limit: int = 100) -> List[Dict]:
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
            result = []
            for record in records:
                record_dict = dict(record)
                # Désérialise le JSON si c'est une chaîne
                if isinstance(record_dict['content'], str):
                    try:
                        record_dict['content'] = json.loads(record_dict['content'])
                    except json.JSONDecodeError:
                        logger.warning(f"Impossible de désérialiser le contenu pour l'ID {record_dict['id']}")
                result.append(record_dict)
            return result
    except Exception as e:
        logger.error(f"Erreur de récupération: {str(e)}")
        return []

async def clear_remote_history(user_id: int) -> None:
    try:
        async with _PG_POOL.acquire() as conn:
            await conn.execute('DELETE FROM memories WHERE user_id = $1', user_id)
    except Exception as e:
        logger.error(f"Erreur de suppression: {str(e)}")
        raise

def _generate_embedding(text: str) -> List[float]:
    if not _EMBEDDER:
        raise ValueError("Embedder non initialisé")
    try:
        return list(_EMBEDDER.embed([text]))[0].tolist()
    except Exception as e:
        logger.error(f"Erreur d'embedding: {str(e)}")
        raise

def _vec_to_str(vec: List[float]) -> str:
    return '[' + ','.join(f"{x:.8f}" for x in vec) + ']'

async def initialize() -> None:
    await connect_to_db()
    initialize_embedder()
    await init_db()

async def search_similar_memories(user_id: int, server_id: int, query: str, limit: int = 5) -> List[Dict]:
    """Recherche des mémoires similaires basée sur la similarité vectorielle"""
    await _delete_old_memories()
    try:
        query_embedding = _generate_embedding(query)
        query_vec_str = _vec_to_str(query_embedding)
        
        async with _PG_POOL.acquire() as conn:
            records = await conn.fetch('''
                SELECT id, content, created_at, 
                       embedding <-> $1::vector as distance
                FROM memories 
                WHERE user_id = $2 AND server_id = $3
                ORDER BY distance ASC
                LIMIT $4
            ''', query_vec_str, user_id, server_id, limit)
            result = []
            for record in records:
                record_dict = dict(record)
                # Désérialise le JSON si c'est une chaîne
                if isinstance(record_dict['content'], str):
                    try:
                        record_dict['content'] = json.loads(record_dict['content'])
                    except json.JSONDecodeError:
                        logger.warning(f"Impossible de désérialiser le contenu pour l'ID {record_dict['id']}")
                result.append(record_dict)
            return result
    except Exception as e:
        logger.error(f"Erreur de recherche vectorielle: {str(e)}")
        return []

async def get_contextual_history(user_id: int, server_id: int, current_query: str, limit: int) -> List[Dict]:
    """Récupère l'historique le plus pertinent basé sur la requête actuelle"""
    await _delete_old_memories()
    try:
        query_embedding = _generate_embedding(current_query)
        query_vec_str = _vec_to_str(query_embedding)
        
        async with _PG_POOL.acquire() as conn:
            # Combine recherche par similarité et récence
            records = await conn.fetch('''
                SELECT id, content, created_at, 
                       embedding <-> $1::vector as distance
                FROM memories 
                WHERE user_id = $2 AND server_id = $3
                ORDER BY distance ASC, created_at DESC
                LIMIT $4
            ''', query_vec_str, user_id, server_id, limit)
            result = []
            for record in records:
                record_dict = dict(record)
                # Désérialise le JSON si c'est une chaîne
                if isinstance(record_dict['content'], str):
                    try:
                        record_dict['content'] = json.loads(record_dict['content'])
                    except json.JSONDecodeError:
                        logger.warning(f"Impossible de désérialiser le contenu pour l'ID {record_dict['id']}")
                result.append(record_dict)
            return result
    except Exception as e:
        logger.error(f"Erreur de récupération contextuelle: {str(e)}")
        # Fallback vers l'historique chronologique
        return await get_history(user_id, server_id, limit)

async def get_hybrid_history(user_id: int, server_id: int, current_query: str, recent_limit: int = 3, similar_limit: int = 5) -> List[Dict]:
    """Combine historique récent et mémoires similaires pour un contexte optimal"""
    await _delete_old_memories()
    try:
        # Récupère les messages les plus récents
        recent_memories = await get_history(user_id, server_id, recent_limit)
        
        # Si pas assez de mémoires récentes, retourne juste l'historique contextuel
        if len(recent_memories) < 2:
            return await get_contextual_history(user_id, server_id, current_query, recent_limit + similar_limit)
        
        # Récupère les mémoires similaires (en excluant les récentes)
        recent_ids = [mem['id'] for mem in recent_memories]
        
        query_embedding = _generate_embedding(current_query)
        query_vec_str = _vec_to_str(query_embedding)
        
        async with _PG_POOL.acquire() as conn:
            if recent_ids:
                # Crée la requête avec les bons placeholders
                id_placeholders = ','.join([f'${i+4}' for i in range(len(recent_ids))])
                limit_param = f'${len(recent_ids) + 4}'
                query_sql = f'''
                    SELECT id, content, created_at, 
                           embedding <-> $1::vector as distance
                    FROM memories 
                    WHERE user_id = $2 AND server_id = $3
                    AND id NOT IN ({id_placeholders})
                    ORDER BY distance ASC
                    LIMIT {limit_param}
                '''
                similar_records = await conn.fetch(query_sql, query_vec_str, user_id, server_id, *recent_ids, similar_limit)
            else:
                # Pas de mémoires récentes à exclure
                similar_records = await conn.fetch('''
                    SELECT id, content, created_at, 
                           embedding <-> $1::vector as distance
                    FROM memories 
                    WHERE user_id = $2 AND server_id = $3
                    ORDER BY distance ASC
                    LIMIT $4
                ''', query_vec_str, user_id, server_id, similar_limit)
            
            similar_memories = []
            for record in similar_records[:similar_limit]:
                record_dict = dict(record)
                # Désérialise le JSON si c'est une chaîne
                if isinstance(record_dict['content'], str):
                    try:
                        record_dict['content'] = json.loads(record_dict['content'])
                    except json.JSONDecodeError:
                        logger.warning(f"Impossible de désérialiser le contenu pour l'ID {record_dict['id']}")
                similar_memories.append(record_dict)
        
        # Combine et trie par pertinence
        all_memories = recent_memories + similar_memories
        return all_memories
        
    except Exception as e:
        logger.error(f"Erreur de récupération hybride: {str(e)}")
        return await get_history(user_id, server_id, recent_limit + similar_limit)
