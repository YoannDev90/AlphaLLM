"""RAG Document Handler - Chunking, Embedding, and Semantic Search"""

import logging
import chromadb
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib
import time
from utils.config.app_config import CHROMA_DB_NAME, CHROMA_TENANT_ID, CHROMA_API_KEY
from utils.memory.embedder import TextEmbedder

logger = logging.getLogger("AlphaLLM.RAG")


class DocumentChunker:
    """Splits documents into semantic chunks with configurable size"""
    
    def __init__(self, chunk_size: int = 256, overlap: int = 50):
        """Initialize chunker
        
        Args:
            chunk_size: Target chunk size in approximate tokens (256-512)
            overlap: Number of overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.avg_chars_per_token = 4.5  # Average English estimate
        logger.debug(f"DocumentChunker initialized: chunk_size={chunk_size}, overlap={overlap}")
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from character count
        
        Args:
            text: Text to estimate
            
        Returns:
            Approximate token count
        """
        return int(len(text) / self.avg_chars_per_token)
    
    def chunk_by_token_count(self, text: str) -> List[str]:
        """Split text into chunks by approximate token count
        
        Args:
            text: Document text to chunk
            
        Returns:
            List of text chunks
        """
        logger.debug(f"Chunking text of {len(text)} chars")
        
        sentences = text.replace('\n\n', '.\n').split('.')
        chunks = []
        current_chunk = []
        current_tokens = 0
        target_size = self.chunk_size
        overlap_size = self.overlap
        
        for sentence in sentences:
            sentence = sentence.strip() + '.'
            if not sentence.strip():
                continue
                
            sentence_tokens = self.estimate_tokens(sentence)
            
            # If Adding this sentence exceeds limit, start new chunk
            if current_tokens + sentence_tokens > target_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                logger.debug(f"Chunk created: {self.estimate_tokens(chunk_text)} tokens")
                
                # Keep overlap: retain some sentences for context
                if len(current_chunk) > 1:
                    current_chunk = current_chunk[-max(1, len(current_chunk) // 2):]
                    current_tokens = sum(
                        self.estimate_tokens(s) for s in current_chunk
                    )
                else:
                    current_chunk = []
                    current_tokens = 0
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
            logger.debug(f"Final chunk created: {self.estimate_tokens(chunk_text)} tokens")
        
        logger.info(f"Document split into {len(chunks)} chunks")
        return chunks
    
    def chunk_by_paragraph(self, text: str) -> List[str]:
        """Split by paragraphs and merge to target size
        
        Args:
            text: Document text to chunk
            
        Returns:
            List of text chunks
        """
        logger.debug("Chunking by paragraphs")
        
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self.estimate_tokens(para)
            
            if current_tokens + para_tokens > self.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(chunk_text)
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append(para)
            current_tokens += para_tokens
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        logger.info(f"Document split into {len(chunks)} paragraph chunks")
        return chunks


class RAGHandler:
    """Manages RAG document storage and retrieval"""
    
    def __init__(self, embedder: Optional[TextEmbedder] = None):
        """Initialize RAG handler
        
        Args:
            embedder: TextEmbedder instance
        """
        logger.debug("Initializing RAGHandler")
        self.embedder = embedder or TextEmbedder()
        self.chunker = DocumentChunker(chunk_size=256, overlap=50)
        self.chroma_client = None
        self.rag_collection = None
        self._embedding_cache = {}
        logger.debug("RAGHandler initialized")
    
    async def initialize(self) -> None:
        """Initialize ChromaDB connection and RAG collection"""
        try:
            logger.debug("Initializing ChromaDB for RAG...")
            self.chroma_client = chromadb.CloudClient(
                tenant=CHROMA_TENANT_ID,
                database=CHROMA_DB_NAME,
                api_key=CHROMA_API_KEY
            )
            
            self.rag_collection = self.chroma_client.get_or_create_collection("rag_documents")
            logger.info("ChromaDB RAG collection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB for RAG: {str(e)}")
            raise
    
    def _generate_chunk_id(self, user_id: int, server_id: int, doc_id: str, chunk_index: int) -> str:
        """Generate unique ID for a document chunk
        
        Args:
            user_id: User ID
            server_id: Server ID
            doc_id: Document ID
            chunk_index: Index of chunk in document
            
        Returns:
            Unique hash ID
        """
        base = f"rag:{user_id}:{server_id}:{doc_id}:{chunk_index}:{time.time_ns()}"
        return hashlib.sha256(base.encode()).hexdigest()
    
    async def add_document(self, user_id: int, server_id: int, document_text: str, 
                          document_id: str, metadata: Optional[Dict] = None) -> Tuple[str, int]:
        """Add a document to RAG collection with chunking
        
        Args:
            user_id: User ID
            server_id: Server ID
            document_text: Full document text
            document_id: Unique document identifier
            metadata: Optional metadata dict
            
        Returns:
            Tuple of (document_id, number_of_chunks)
        """
        logger.debug(f"Adding document {document_id} for user={user_id}, server={server_id}")
        
        try:
            # Chunk the document
            chunks = self.chunker.chunk_by_token_count(document_text)
            logger.debug(f"Document split into {len(chunks)} chunks")
            
            if not chunks:
                logger.warning("Document produced no chunks")
                return document_id, 0
            
            # Prepare storage
            chunk_ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            base_metadata = {
                "user_id": user_id,
                "server_id": server_id,
                "document_id": document_id,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.embedder.embed(chunk)
                
                # Create metadata
                chunk_metadata = {
                    **base_metadata,
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                    "chunk_size_tokens": self.chunker.estimate_tokens(chunk)
                }
                
                chunk_id = self._generate_chunk_id(user_id, server_id, document_id, i)
                
                chunk_ids.append(chunk_id)
                embeddings.append(embedding)
                documents.append(chunk)
                metadatas.append(chunk_metadata)
                
                chunk_size_tokens = chunk_metadata["chunk_size_tokens"]
                logger.debug(f"Chunk {i+1}/{len(chunks)} prepared: {chunk_size_tokens} tokens")
            
            # Store all chunks
            self.rag_collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Document {document_id} stored with {len(chunks)} chunks")
            return document_id, len(chunks)
            
        except Exception as e:
            logger.error(f"Error Adding document: {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            raise
    
    async def retrieve_relevant_chunks(self, user_id: int, server_id: int, query: str,
                                       k: int = 5, min_relevance: float = 0.3) -> List[Dict]:
        """Retrieve top-K relevant document chunks
        
        Args:
            user_id: User ID
            server_id: Server ID
            query: Search query
            k: Number of chunks to retrieve
            min_relevance: Minimum similarity score (0-1)
            
        Returns:
            List of relevant chunks with metadata
        """
        logger.debug(f"Retrieving {k} relevant chunks for query: '{query[:50]}...'")
        
        try:
            # Embed query
            query_embedding = self.embedder.embed(query)
            
            # Search
            results = self.rag_collection.query(
                query_embeddings=[query_embedding],
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}}
                    ]
                },
                n_results=k,
                include=["metadatas", "documents", "distances"]
            )
            
            # Format results
            retrieved = []
            if results.get("ids") and results["ids"][0]:
                for i, chunk_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    # Convert distance to similarity (0=most similar)
                    similarity = 1 - (distance / 2)  # Normalize to 0-1
                    
                    if similarity >= min_relevance:
                        retrieved.append({
                            "id": chunk_id,
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "relevance_score": similarity,
                            "distance": distance
                        })
                        logger.debug(f"Chunk retrieved: relevance={similarity:.3f}")
            
            logger.info(f"Retrieved {len(retrieved)} relevant chunks (min_relevance={min_relevance})")
            return retrieved
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return []
    
    async def get_document_summary(self, user_id: int, server_id: int, 
                                   document_id: str) -> Optional[Dict]:
        """Get document info and chunks
        
        Args:
            user_id: User ID
            server_id: Server ID
            document_id: Document ID to retrieve
            
        Returns:
            Document info with all chunks or None
        """
        logger.debug(f"Retrieving document {document_id}")
        
        try:
            results = self.rag_collection.get(
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}},
                        {"document_id": {"$eq": document_id}}
                    ]
                },
                include=["metadatas", "documents"]
            )
            
            if not results.get("ids"):
                logger.warning(f"Document {document_id} not found")
                return None
            
            # Reconstruct document
            chunks = []
            for i, chunk_id in enumerate(results["ids"]):
                chunks.append({
                    "index": results["metadatas"][i].get("chunk_index", i),
                    "content": results["documents"][i],
                    "size_tokens": results["metadatas"][i].get("chunk_size_tokens", 0)
                })
            
            summary = {
                "document_id": document_id,
                "created_at": results["metadatas"][0].get("created_at"),
                "chunk_count": len(chunks),
                "total_tokens": sum(c["size_tokens"] for c in chunks),
                "chunks": chunks
            }
            
            logger.info(f"Document retrieved: {len(chunks)} chunks, {summary['total_tokens']} tokens")
            return summary
            
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return None
    
    async def delete_document(self, user_id: int, server_id: int, document_id: str) -> int:
        """Delete all chunks of a document
        
        Args:
            user_id: User ID
            server_id: Server ID
            document_id: Document ID to delete
            
        Returns:
            Number of chunks deleted
        """
        logger.debug(f"Deleting document {document_id}")
        
        try:
            results = self.rag_collection.get(
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"server_id": {"$eq": server_id}},
                        {"document_id": {"$eq": document_id}}
                    ]
                }
            )
            
            if results.get("ids"):
                self.rag_collection.delete(ids=results["ids"])
                logger.info(f"Document deleted: {len(results['ids'])} chunks removed")
                return len(results["ids"])
            
            logger.debug(f"No chunks found for document {document_id}")
            return 0
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            raise
    
    async def search_documents(self, user_id: int, server_id: int, query: str,
                              limit: int = 10) -> Dict[str, List]:
        """Search across all documents
        
        Args:
            user_id: User ID
            server_id: Server ID
            query: Search query
            limit: Maximum results
            
        Returns:
            Dictionary with search results grouped by document
        """
        logger.debug(f"Searching documents for: '{query[:50]}...'")
        
        chunks = await self.retrieve_relevant_chunks(user_id, server_id, query, k=limit)
        
        # Group by document
        grouped = {}
        for chunk in chunks:
            doc_id = chunk["metadata"].get("document_id", "unknown")
            if doc_id not in grouped:
                grouped[doc_id] = []
            grouped[doc_id].append(chunk)
        
        logger.info(f"Search found {len(chunks)} chunks across {len(grouped)} documents")
        return grouped


# Global RAG handler instance
_rag_handler: Optional[RAGHandler] = None


async def initialize_rag() -> None:
    """Initialize global RAG handler"""
    global _rag_handler
    logger.debug("Initializing global RAG handler")
    _rag_handler = RAGHandler()
    await _rag_handler.initialize()


def get_rag_handler() -> RAGHandler:
    """Get global RAG handler
    
    Raises:
        RuntimeError: If not initialized
    """
    global _rag_handler
    if _rag_handler is None:
        raise RuntimeError("RAG handler not initialized. Call initialize_rag() first.")
    return _rag_handler
