import chromadb
from utils.config import CHROMA_DB_NAME, CHROMA_TENANT_ID, CHROMA_API_KEY, EMBEDDER_MODEL, MEMORY_DURATION, RECENT_LIMIT
import logging
from typing import List, Dict, Any
from fastembed import TextEmbedding
import time
from datetime import datetime, timedelta
import json
import hashlib

logger = logging.getLogger("memory_ai")

def initialize_chroma_client():
    return chromadb.CloudClient(
        tenant=CHROMA_TENANT_ID,
        database=CHROMA_DB_NAME,
        api_key=CHROMA_API_KEY
    )

async def initialize() -> None:
    global chroma_client, collection
    try:
        chroma_client = initialize_chroma_client()
        collection = chroma_client.get_or_create_collection("memories")
        logger.info("ChromaDB Cloud initialisé avec succès")
    except Exception as e:
        logger.critical(f"Échec de connexion à ChromaDB Cloud : {str(e)}")
        raise

def generate_embedding(text: str) -> List[float]:
    embedder = TextEmbedding(model_name=EMBEDDER_MODEL)
    try:
        return list(embedder.embed([text]))[0].tolist()
    except Exception as e:
        logger.error(f"Erreur d'embedding: {str(e)}")
        raise

def generate_id(user_id: int, server_id: int) -> str:
    base = f"{user_id}:{server_id}:{time.time_ns()}"
    return hashlib.sha256(base.encode()).hexdigest()

async def add_memory(user_id: int, server_id: int, reponse: dict, text_to_embed: str) -> None:
    await delete_old_memories()
    try:
        embedding_vector = generate_embedding(text_to_embed)
        entry_id = generate_id(user_id, server_id)
        
        collection.add(
            ids=[entry_id],
            embeddings=[embedding_vector],
            documents=[text_to_embed],
            metadatas=[{
                "user_id": user_id,
                "server_id": server_id,
                "content": json.dumps(reponse, ensure_ascii=False),
                "created_at": datetime.utcnow().isoformat()
            }]
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de mémoire : {str(e)}")
        raise


async def get_history(user_id: int, server_id: int, limit: int = 100) -> List[Dict]:
    await delete_old_memories()
    try:
        results = collection.get(
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"server_id": {"$eq": server_id}}
                ]
            },
            limit=limit,
            include=["metadatas", "documents"]
        )
        return format_results(results)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique : {str(e)}")
        return []


async def search_similar_memories(user_id: int, server_id: int, query: str, limit: int = 5) -> List[Dict]:
    await delete_old_memories()
    try:
        query_embedding = generate_embedding(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"server_id": {"$eq": server_id}}
                ]
            },
            n_results=limit,
            include=["metadatas", "documents"]
        )
        return format_results(results)
    except Exception as e:
        logger.error(f"Erreur lors de la recherche vectorielle : {str(e)}")
        return []
    
async def get_hybrid_history(user_id: int, server_id: int, current_query: str, recent_limit: int = 3, similar_limit: int = 5) -> List[Dict]:
    await delete_old_memories()
    
    recent_memories = await get_history(user_id, server_id, recent_limit)
    if len(recent_memories) < 2:
        return await search_similar_memories(user_id, server_id, current_query, recent_limit + similar_limit)
    
    similar_memories = await search_similar_memories(user_id, server_id, current_query, similar_limit)
    
    seen_ids = {mem["id"] for mem in recent_memories}
    unique_similar = [m for m in similar_memories if m["id"] not in seen_ids]
    
    return recent_memories + unique_similar[:similar_limit]

async def delete_old_memories() -> None:
    try:
        all_memories = collection.get(
            include=["metadatas"]
        )
        if not all_memories["metadatas"]:
            return
        
        now = datetime.now().timestamp()
        expired_ids = []
        
        for i, meta in enumerate(all_memories["metadatas"]):
            created_at = datetime.fromisoformat(meta["created_at"]).timestamp()
            if now - created_at > MEMORY_DURATION:
                # Utiliser l'ID de la liste des IDs au même index
                expired_ids.append(all_memories["ids"][i])
        
        if expired_ids:
            collection.delete(ids=expired_ids)
            logger.info(f"Suppression de {len(expired_ids)} mémoires expirées")
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des mémoires : {str(e)}")


def format_results(results: Dict) -> List[Dict]:
    formatted = []
    
    # ChromaDB retourne les résultats différemment selon la méthode (get vs query)
    # Pour collection.get(): {"metadatas": [...], "documents": [...], "ids": [...]}
    # Pour collection.query(): {"metadatas": [[...]], "documents": [[...]], "ids": [[...]]}
    
    metadatas = results.get("metadatas", [])
    documents = results.get("documents", [])
    ids = results.get("ids", [])
    
    # Si c'est un résultat de query (liste de listes), on prend le premier élément
    if metadatas and isinstance(metadatas[0], list):
        metadatas = metadatas[0] if metadatas else []
        documents = documents[0] if documents else []
        ids = ids[0] if ids else []
    
    for meta, doc, entry_id in zip(metadatas, documents, ids):
        try:
            content = json.loads(meta["content"]) if isinstance(meta["content"], str) else meta["content"]
        except (json.JSONDecodeError, KeyError):
            content = meta.get("content", doc)
        formatted.append({
            "id": entry_id,
            "content": content,
            "created_at": meta.get("created_at"),
            "text": doc
        })
    return formatted

async def clear_remote_history(user_id: int) -> None:
    try:
        results = collection.get(
            where={"user_id": {"$eq": user_id}}
        )
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
        logger.info(f"Historique utilisateur {user_id} supprimé")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'historique : {str(e)}")


