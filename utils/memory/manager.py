"""Gestionnaire de mémoire avec ChromaDB (STM + LTM + RAG)"""

import chromadb
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import hashlib
import time
import os

from utils.config.app_config import CHROMA_DB_NAME, CHROMA_TENANT_ID, CHROMA_API_KEY, MEMORY_DURATION
from utils.memory.embedder import TextEmbedder
from utils.memory.config import STM_MAX_AGE, LTM_MIN_SIMILARITY

logger = logging.getLogger("AlphaLLM")

# Disable ChromaDB telemetry to avoid "capture() takes 1 positional argument but 3 were given" error
os.environ["CHROMA_TELEMETRY_DISABLED"] = "true"


class MemoryManager:
    """Gestionnaire de mémoire avec STM (court-terme) et LTM (long-terme)"""
    
    def __init__(self, embedder: Optional[TextEmbedder] = None):
        """Initialise le gestionnaire de mémoires
        
        Args:
            embedder: Instance de TextEmbedder (crée une nouvelle si None)
        """
        logger.debug("Initialisation de MemoryManager (STM + LTM)")
        self.embedder = embedder or TextEmbedder()
        self.chroma_client = None
        self.stm_collection = None  # Short-Term Memory (messages de conversation)
        self.ltm_collection = None  # Long-Term Memory (faits importants, préférences)
        logger.debug("MemoryManager initialisé")
    
    async def initialize(self) -> None:
        """Initialise la connexion à ChromaDB Cloud et les trois collections"""
        try:
            logger.debug("Initialisation de ChromaDB Cloud...")
            self.chroma_client = chromadb.CloudClient(
                tenant=CHROMA_TENANT_ID,
                database=CHROMA_DB_NAME,
                api_key=CHROMA_API_KEY
            )
            logger.debug(f"Connexion à ChromaDB Cloud établie (tenant: {CHROMA_TENANT_ID}, db: {CHROMA_DB_NAME})")
            
            # create les trois collections
            self.stm_collection = self.chroma_client.get_or_create_collection("stm_memories")  # Court-terme
            self.ltm_collection = self.chroma_client.get_or_create_collection("ltm_memories")  # Long-terme
            # RAG collection créée séparément dans rag_handler.py
            
            logger.debug("ChromaDB Cloud initialisé avec succès (STM + LTM)")
            logger.debug("Collections 'stm_memories' et 'ltm_memories' récupérées ou créées")
        except Exception as e:
            logger.error(f"Échec de connexion à ChromaDB Cloud : {str(e)}")
            logger.debug(f"Stack trace de l'erreur ChromaDB: {e}", exc_info=True)
            raise
    
    def _generate_id(self, user_id: int, server_id: int, prefix: str = "") -> str:
        """Génère un ID unique pour une mémoire
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur
            prefix: Préfixe optionnel (stm, ltm, etc)
            
        Returns:
            Hash SHA256 unique
        """
        base = f"{prefix}:{user_id}:{server_id}:{time.time_ns()}"
        entry_id = hashlib.sha256(base.encode()).hexdigest()
        logger.debug(f"ID généré pour user={user_id}, server={server_id}, prefix={prefix}: {entry_id}")
        return entry_id
    
    async def _delete_old_stm_memories(self, user_id: int, server_id: int) -> None:
        """Supprime les mémoires STM expirées pour un utilisateur/serveur"""
        try:
            logger.debug(f"Nettoyage des mémoires STM expirées pour user={user_id}, server={server_id}...")
            all_memories = self.stm_collection.get(
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}}
                    ]
                },
                include=["metadatas"]
            )
            
            if not all_memories["metadatas"]:
                logger.debug("Aucune mémoire STM pour cet utilisateur")
                return
            
            now = datetime.utcnow().timestamp()
            expired_ids = []
            
            for i, meta in enumerate(all_memories["metadatas"]):
                created_at = datetime.fromisoformat(meta["created_at"]).timestamp()
                age = now - created_at
                if age > STM_MAX_AGE:
                    expired_ids.append(all_memories["ids"][i])
                    logger.debug(f"Mémoire STM {all_memories['ids'][i]} expirée: age={age:.1f}s")
            
            if expired_ids:
                logger.debug(f"Suppression de {len(expired_ids)} mémoires STM expirées")
                self.stm_collection.delete(ids=expired_ids)
                logger.info(f"Suppression de {len(expired_ids)} mémoires STM expirées")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage STM : {str(e)}")
            logger.debug(f"Cleanup stack trace STM: {e}", exc_info=True)
    
    async def add_conversation_message(self, user_id: int, server_id: int, text: str, role: str = "user") -> str:
        """Ajoute un message de conversation à la STM
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur
            text: Texte du message (résumé si long)
            role: "user" ou "assistant"
            
        Returns:
            L'ID du message ajouté
        """
        logger.debug(f"Ajout message de conversation pour user={user_id}, server={server_id}, role={role}")
        await self._delete_old_stm_memories(user_id, server_id)
        
        try:
            embedding = self.embedder.embed(text)
            entry_id = self._generate_id(user_id, server_id, prefix="stm")
            
            self.stm_collection.add(
                ids=[entry_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "user_id": user_id,
                    "server_id": server_id,
                    "role": role,
                    "created_at": datetime.utcnow().isoformat()
                }]
            )
            logger.debug(f"Message STM ajouté: ID={entry_id}, role={role}")
            return entry_id
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du message conversation : {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            raise
    
    async def add_long_term_memory(self, user_id: int, server_id: int, title: str, content: str, category: str = "general") -> str:
        """Ajoute une mémoire long-terme (faits importants, préférences, etc)
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur
            title: Titre/résumé court de la mémoire
            content: Contenu détaillé
            category: Catégorie (general, preferences, facts, etc)
            
        Returns:
            L'ID de la mémoire ajoutée
        """
        logger.debug(f"Ajout LTM pour user={user_id}, server={server_id}, category={category}")
        
        try:
            # Utiliser le contenu pour l'embedding
            embedding = self.embedder.embed(content)
            entry_id = self._generate_id(user_id, server_id, prefix="ltm")
            
            self.ltm_collection.add(
                ids=[entry_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    "user_id": user_id,
                    "server_id": server_id,
                    "title": title,
                    "category": category,
                    "created_at": datetime.utcnow().isoformat()
                }]
            )
            logger.debug(f"Mémoire LTM ajoutée: ID={entry_id}, category={category}")
            return entry_id
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout LTM : {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            raise
    
    async def update_long_term_memory(self, user_id: int, server_id: int, title: str, content: str, category: str = "general") -> str:
        """Met à jour ou crée une mémoire LTM (remplace si le titre existe déjà)
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur
            title: Titre/clé de la mémoire
            content: Contenu/valeur
            category: Catégorie
            
        Returns:
            L'ID de la mémoire (nouveau ou existant)
        """
        logger.debug(f"Mise à jour LTM pour user={user_id}, title={title}")
        
        try:
            # search un fait existant avec le même titre
            existing = self.ltm_collection.get(
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}},
                        {"title": {"$eq": title}}
                    ]
                }
            )
            
            embedding = self.embedder.embed(content)
            new_metadata = {
                "user_id": user_id,
                "server_id": server_id,
                "title": title,
                "category": category,
                "created_at": datetime.utcnow().isoformat()
            }
            
            if existing["ids"]:
                # Mettre à jour l'existant
                entry_id = existing["ids"][0]
                logger.debug(f"Mise à jour de LTM existante: ID={entry_id}")
                self.ltm_collection.update(
                    ids=[entry_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[new_metadata]
                )
            else:
                # create une nouvelle entrée
                entry_id = self._generate_id(user_id, server_id, prefix="ltm")
                logger.debug(f"Création de nouvelle LTM: ID={entry_id}")
                self.ltm_collection.add(
                    ids=[entry_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[new_metadata]
                )
            
            logger.debug(f"LTM mise à jour: ID={entry_id}, title={title}")
            return entry_id
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour LTM : {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            raise
    
    async def add_document(self, user_id: int, server_id: int, text_clair: str, text_embed: str) -> bool:
        """Ajoute un document à la mémoire (LTM si pertinent)
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur
            text_clair: Texte lisible du document
            text_embed: Texte pour l'embedding (peut être différent, ex: résumé)
            
        Returns:
            True si le document a été ajouté, False s'il n'est pas pertinent
        """
        logger.debug(f"Évaluation de pertinence du document pour user={user_id}, server={server_id}")
        
        try:
            # Pour déterminer la pertinence, on fait une recherche vectorielle simple
            # if the document a une forte similarité avec des contenus existants, on le considère comme peu pertinent
            embedding = self.embedder.embed(text_embed)
            
            # Rechercher des documents similaires dans la LTM
            logger.debug("Recherche de documents similaires existants...")
            results = self.ltm_collection.query(
                query_embeddings=[embedding],
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}}
                    ]
                },
                n_results=3,
                include=["metadatas", "documents", "distances"]
            )
            
            # Si distances sont trop petites (< 0.3), le document est redondant
            if results.get("distances") and results["distances"][0]:
                min_distance = min(results["distances"][0])
                logger.debug(f"Distance minimale trouvée: {min_distance}")
                
                if min_distance < LTM_MIN_SIMILARITY:
                    logger.info(f"Document peu pertinent (distance: {min_distance}), non ajouté")
                    return False
            
            # Document pertinent, l'add à la LTM
            logger.debug("Document pertinent, ajout à la LTM")
            await self.add_long_term_memory(
                user_id,
                server_id,
                title=text_clair[:100],  # Titre = premiers 100 chars
                content=text_embed,
                category="document"
            )
            logger.info("Document ajouté à la LTM")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du document : {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return False
    
    async def add_memory(self, user_id: int, server_id: int, text_to_embed: str) -> str:
        """Ajoute une nouvelle mémoire (compatibilité: ajoutée en STM)
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur
            text_to_embed: Texte à mémoriser
            
        Returns:
            L'ID de la mémoire ajoutée
        """
        logger.debug("add_memory() appelé - compatibilité, utilisation add_conversation_message()")
        return await self.add_conversation_message(user_id, server_id, text_to_embed, role="system")
    
    async def get_memories(self, user_id: int, server_id: int, limit_stm: int = 5, limit_ltm: int = 3) -> Dict:
        """Récupère les mémoires STM et LTM récentes
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur
            limit_stm: Nombre de messages STM à retourner
            limit_ltm: Nombre de mémoires LTM à retourner
            
        Returns:
            Dictionnaire avec 'stm' et 'ltm' contenant les mémoires
        """
        logger.debug(f"Récupération des mémoires pour user={user_id}, server={server_id}")
        await self._delete_old_stm_memories(user_id, server_id)
        
        try:
            result = {"stm": [], "ltm": []}
            
            # Récupérer STM
            logger.debug(f"Récupération STM (limit={limit_stm})")
            stm_results = self.stm_collection.get(
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}}
                    ]
                },
                limit=limit_stm,
                include=["metadatas", "documents"]
            )
            
            for i, entry_id in enumerate(stm_results.get("ids", [])):
                result["stm"].append({
                    "id": entry_id,
                    "text": stm_results["documents"][i],
                    "role": stm_results["metadatas"][i].get("role"),
                    "created_at": stm_results["metadatas"][i].get("created_at")
                })
            
            # Récupérer LTM
            logger.debug(f"Récupération LTM (limit={limit_ltm})")
            ltm_results = self.ltm_collection.get(
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}}
                    ]
                },
                limit=limit_ltm,
                include=["metadatas", "documents"]
            )
            
            for i, entry_id in enumerate(ltm_results.get("ids", [])):
                result["ltm"].append({
                    "id": entry_id,
                    "title": ltm_results["metadatas"][i].get("title"),
                    "content": ltm_results["documents"][i],
                    "category": ltm_results["metadatas"][i].get("category"),
                    "created_at": ltm_results["metadatas"][i].get("created_at")
                })
            
            logger.debug(f"Mémoires récupérées: {len(result['stm'])} STM, {len(result['ltm'])} LTM")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des mémoires : {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return {"stm": [], "ltm": []}
    
    async def get_long_term_memories(self, user_id: int, server_id: int, limit: int = 100) -> list:
        """Récupère TOUTES les mémoires LTM pour un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur
            limit: Nombre max de résultats
            
        Returns:
            Liste des mémoires LTM avec tous les détails
        """
        logger.debug(f"Récupération LTM complète pour user={user_id}, server={server_id}")
        
        try:
            ltm_results = self.ltm_collection.get(
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}}
                    ]
                },
                limit=limit,
                include=["metadatas", "documents"]
            )
            
            result = []
            for i, entry_id in enumerate(ltm_results.get("ids", [])):
                result.append({
                    "id": entry_id,
                    "title": ltm_results["metadatas"][i].get("title"),
                    "content": ltm_results["documents"][i],
                    "category": ltm_results["metadatas"][i].get("category"),
                    "created_at": ltm_results["metadatas"][i].get("created_at")
                })
            
            logger.debug(f"LTM complète récupérée: {len(result)} faits")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la récupération LTM : {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return []
    
    async def search_memories(self, user_id: int, server_id: int, query: str, limit: int = 5, memory_type: str = "both") -> Dict:
        """Recherche des mémoires similaires
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur
            query: Texte de requête
            limit: Nombre de résultats
            memory_type: "stm", "ltm" ou "both"
            
        Returns:
            Dictionnaire avec résultats de recherche
        """
        logger.debug(f"Recherche de mémoires similaires pour query={query[:50]}, type={memory_type}")
        
        try:
            embedding = self.embedder.embed(query)
            result = {"stm": [], "ltm": []}
            
            # Rechercher dans STM
            if memory_type in ["stm", "both"]:
                logger.debug(f"Recherche vectorielle STM")
                stm_results = self.stm_collection.query(
                    query_embeddings=[embedding],
                    where={
                        "$and": [
                            {"user_id": {"$eq": user_id}},
                            {"server_id": {"$eq": server_id}}
                        ]
                    },
                    n_results=limit,
                    include=["metadatas", "documents"]
                )
                
                for i, entry_id in enumerate(stm_results.get("ids", [[]])[0]):
                    result["stm"].append({
                        "id": entry_id,
                        "text": stm_results["documents"][0][i],
                        "role": stm_results["metadatas"][0][i].get("role"),
                        "created_at": stm_results["metadatas"][0][i].get("created_at")
                    })
            
            # Rechercher dans LTM
            if memory_type in ["ltm", "both"]:
                logger.debug(f"Recherche vectorielle LTM")
                ltm_results = self.ltm_collection.query(
                    query_embeddings=[embedding],
                    where={
                        "$and": [
                            {"user_id": {"$eq": user_id}},
                            {"server_id": {"$eq": server_id}}
                        ]
                    },
                    n_results=limit,
                    include=["metadatas", "documents"]
                )
                
                for i, entry_id in enumerate(ltm_results.get("ids", [[]])[0]):
                    result["ltm"].append({
                        "id": entry_id,
                        "title": ltm_results["metadatas"][0][i].get("title"),
                        "content": ltm_results["documents"][0][i],
                        "category": ltm_results["metadatas"][0][i].get("category"),
                        "created_at": ltm_results["metadatas"][0][i].get("created_at")
                    })
            
            logger.debug(f"Résultats: {len(result['stm'])} STM, {len(result['ltm'])} LTM")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la recherche : {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return {"stm": [], "ltm": []}
    
    async def get_hybrid_memories(self, user_id: int, server_id: int, current_query: str, recent_limit: int = 3, similar_limit: int = 5) -> Dict:
        """Récupère un historique hybride (récent STM + LTM pertinent)
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur
            current_query: Requête actuelle pour la recherche vectorielle
            recent_limit: Nombre de messages STM récents
            similar_limit: Nombre de mémoires LTM pertinentes
            
        Returns:
            Dictionnaire avec 'stm' (récents) et 'ltm' (pertinent)
        """
        logger.debug(f"Récupération de l'historique hybride pour user={user_id}, server={server_id}")
        await self._delete_old_stm_memories(user_id, server_id)
        
        try:
            result = {"stm": [], "ltm": []}
            
            # retrieve les messages STM récents
            logger.debug(f"Étape 1: Récupération des messages STM récents (limit={recent_limit})")
            stm_recent = self.stm_collection.get(
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}}
                    ]
                },
                limit=recent_limit,
                include=["metadatas", "documents"]
            )
            
            for i, entry_id in enumerate(stm_recent.get("ids", [])):
                result["stm"].append({
                    "id": entry_id,
                    "text": stm_recent["documents"][i],
                    "role": stm_recent["metadatas"][i].get("role"),
                    "created_at": stm_recent["metadatas"][i].get("created_at")
                })
            
            logger.debug(f"Messages STM récents trouvés: {len(result['stm'])}")
            
            # Rechercher les mémoires LTM pertinentes basées sur la requête actuelle
            logger.debug(f"Étape 2: Recherche vectorielle LTM pour la requête actuelle (limit={similar_limit})")
            embedding = self.embedder.embed(current_query)
            
            ltm_search = self.ltm_collection.query(
                query_embeddings=[embedding],
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}}
                    ]
                },
                n_results=similar_limit,
                include=["metadatas", "documents"]
            )
            
            for i, entry_id in enumerate(ltm_search.get("ids", [[]])[0]):
                result["ltm"].append({
                    "id": entry_id,
                    "title": ltm_search["metadatas"][0][i].get("title"),
                    "content": ltm_search["documents"][0][i],
                    "category": ltm_search["metadatas"][0][i].get("category"),
                    "created_at": ltm_search["metadatas"][0][i].get("created_at")
                })
            
            logger.debug(f"Mémoires LTM pertinentes trouvées: {len(result['ltm'])}")
            logger.debug(f"Historique hybride final: {len(result['stm'])} STM + {len(result['ltm'])} LTM")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération hybride : {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return {"stm": [], "ltm": []}
    
    async def clear_history(self, user_id: int, server_id: int = None, memory_type: str = "stm") -> int:
        """Supprime l'historique d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            server_id: ID du serveur (optionnel, si None supprime partout)
            memory_type: "stm", "ltm" ou "both"
            
        Returns:
            Nombre d'entrées supprimées
        """
        logger.debug(f"Suppression de l'historique pour user={user_id}, type={memory_type}")
        total_deleted = 0
        
        try:
            where_clause = {"user_id": {"$eq": user_id}}
            if server_id is not None:
                where_clause = {
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}}
                    ]
                }
            
            if memory_type in ["stm", "both"]:
                logger.debug("Suppression des mémoires STM")
                stm_results = self.stm_collection.get(where=where_clause)
                stm_ids = stm_results.get("ids", [])
                if stm_ids:
                    self.stm_collection.delete(ids=stm_ids)
                    logger.info(f"STM supprimée: {len(stm_ids)} entrées")
                    total_deleted += len(stm_ids)
            
            if memory_type in ["ltm", "both"]:
                logger.debug("Suppression des mémoires LTM")
                ltm_results = self.ltm_collection.get(where=where_clause)
                ltm_ids = ltm_results.get("ids", [])
                if ltm_ids:
                    self.ltm_collection.delete(ids=ltm_ids)
                    logger.info(f"LTM supprimée: {len(ltm_ids)} entrées")
                    total_deleted += len(ltm_ids)
            
            logger.info(f"Total supprimé: {total_deleted} entrées")
            return total_deleted
        except Exception as e:
            logger.error(f"Erreur lors de la suppression : {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            raise