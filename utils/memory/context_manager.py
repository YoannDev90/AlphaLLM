"""Context Manager - Hybrid memory retrieval with optimization"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from utils.memory.manager import MemoryManager
from utils.memory.rag_handler import RAGHandler
from utils.memory.prompt_builder import StructuredPromptBuilder

logger = logging.getLogger("AlphaLLM.ContextManager")


class RelevanceScorer:
    """Scores and ranks context items by relevance"""
    
    @staticmethod
    def score_stm_message(message: Dict, query: str = "", recency_weight: float = 0.7) -> float:
        """Score STM message by relevance
        
        Args:
            message: STM message dict
            query: Optional query for semantic relevance (not implemented here)
            recency_weight: Weight for recency (0-1)
            
        Returns:
            Relevance score (0-1)
        """
        # For now, use recency as proxy
        created_at = message.get("created_at")
        if not created_at:
            return 0.5
        
        try:
            msg_time = datetime.fromisoformat(created_at)
            age_hours = (datetime.utcnow() - msg_time).total_seconds() / 3600
            
            # Exponential decay: recent messages score higher
            recency_score = 1.0 / (1.0 + (age_hours / 24))  # Half-life of 24 hours
            
            return min(1.0, recency_score * recency_weight + 0.3)
        except:
            return 0.5
    
    @staticmethod
    def score_ltm_fact(fact: Dict, category_weights: Optional[Dict] = None) -> float:
        """Score LTM fact by importance
        
        Args:
            fact: LTM fact dict
            category_weights: Optional weights for categories
            
        Returns:
            Relevance score (0-1)
        """
        base_weight = {
            "preferences": 0.9,
            "skills": 0.85,
            "background": 0.75,
            "interests": 0.8,
            "constraints": 0.95,  # Constraints are very important
            "contact": 0.7,
            "relationships": 0.8,
            "goals": 0.85,
            "other": 0.5
        }
        
        if category_weights:
            base_weight.update(category_weights)
        
        category = fact.get("category", "other")
        weight = base_weight.get(category, 0.5)
        
        # Apply confidence multiplier if present
        confidence = fact.get("confidence", 1.0)
        
        return weight * confidence
    
    @staticmethod
    def score_rag_chunk(chunk: Dict) -> float:
        """Score RAG chunk by relevance
        
        Args:
            chunk: RAG chunk dict
            
        Returns:
            Relevance score (0-1)
        """
        # Already has relevance_score from retrieval
        return chunk.get("relevance_score", 0.5)


class ContextManager:
    """Manages hybrid memory retrieval combining STM, LTM, and RAG"""
    
    def __init__(self, memory_manager: MemoryManager, rag_handler: RAGHandler,
                 prompt_builder: Optional[StructuredPromptBuilder] = None):
        """Initialize context manager
        
        Args:
            memory_manager: MemoryManager instance
            rag_handler: RAGHandler instance
            prompt_builder: Optional PromptBuilder instance
        """
        self.memory_manager = memory_manager
        self.rag_handler = rag_handler
        self.prompt_builder = prompt_builder or StructuredPromptBuilder()
        self.scorer = RelevanceScorer()
        logger.debug("ContextManager initialized")
    
    async def get_optimized_context(self, user_id: int, server_id: int, query: str,
                                    stm_limit: int = 5, ltm_limit: int = 5,
                                    rag_limit: int = 3, max_tokens: int = 2000) -> Dict:
        """Get optimized context combining all memory types
        
        Args:
            user_id: User ID
            server_id: Server ID
            query: Current query/context
            stm_limit: Max STM messages
            ltm_limit: Max LTM facts
            rag_limit: Max RAG chunks
            max_tokens: Maximum total tokens
            
        Returns:
            Dictionary with optimized context and metadata
        """
        logger.debug(f"Getting optimized context for user={user_id}, query='{query[:50]}...'")
        
        try:
            # Retrieve from all sources in parallel
            memories = await self.memory_manager.get_hybrid_memories(
                user_id, server_id, query,
                recent_limit=stm_limit,
                similar_limit=ltm_limit
            )
            
            rag_chunks = await self.rag_handler.retrieve_relevant_chunks(
                user_id, server_id, query, k=rag_limit
            )
            
            # Score and rank
            stm_scored = [
                (msg, self.scorer.score_stm_message(msg, query))
                for msg in memories.get("stm", [])
            ]
            stm_scored.sort(key=lambda x: x[1], reverse=True)
            
            ltm_scored = [
                (fact, self.scorer.score_ltm_fact(fact))
                for fact in memories.get("ltm", [])
            ]
            ltm_scored.sort(key=lambda x: x[1], reverse=True)
            
            rag_scored = [
                (chunk, self.scorer.score_rag_chunk(chunk))
                for chunk in rag_chunks
            ]
            rag_scored.sort(key=lambda x: x[1], reverse=True)
            
            # Select top items
            selected_stm = [item[0] for item in stm_scored[:stm_limit]]
            selected_ltm = [item[0] for item in ltm_scored[:ltm_limit]]
            selected_rag = [item[0] for item in rag_scored[:rag_limit]]
            
            logger.debug(f"Selected: {len(selected_stm)} STM, {len(selected_ltm)} LTM, {len(selected_rag)} RAG")
            
            # Build context
            context_text = self.prompt_builder.build_memory_context(
                selected_stm, selected_ltm, selected_rag, max_tokens
            )
            
            result = {
                "context": context_text,
                "stm": selected_stm,
                "ltm": selected_ltm,
                "rag": selected_rag,
                "metadata": {
                    "stm_count": len(selected_stm),
                    "ltm_count": len(selected_ltm),
                    "rag_count": len(selected_rag),
                    "context_size": len(context_text),
                    "estimated_tokens": self.prompt_builder.estimate_tokens(context_text)
                }
            }
            
            logger.info(f"Context optimized: {result['metadata']['estimated_tokens']} tokens")
            return result
            
        except Exception as e:
            logger.error(f"Error getting optimized context: {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return {
                "context": "Pas de contexte disponible",
                "stm": [],
                "ltm": [],
                "rag": [],
                "metadata": {"stm_count": 0, "ltm_count": 0, "rag_count": 0, "error": str(e)}
            }
    
    async def get_focused_context(self, user_id: int, server_id: int, query: str,
                                 context_type: str = "all") -> Dict:
        """Get context focused on specific type
        
        Args:
            user_id: User ID
            server_id: Server ID
            query: Query
            context_type: "stm", "ltm", "rag", or "all"
            
        Returns:
            Focused context
        """
        logger.debug(f"Getting focused context: type={context_type}")
        
        result = {"context": "", "metadata": {}}
        
        try:
            if context_type in ["stm", "all"]:
                memories = await self.memory_manager.get_memories(
                    user_id, server_id, limit_stm=10, limit_ltm=0
                )
                stm_text = self.prompt_builder._build_stm_section(memories["stm"])
                result["context"] += stm_text + "\n"
                result["metadata"]["stm_count"] = len(memories["stm"])
            
            if context_type in ["ltm", "all"]:
                memories = await self.memory_manager.get_memories(
                    user_id, server_id, limit_stm=0, limit_ltm=10
                )
                ltm_text = self.prompt_builder._build_ltm_section(memories["ltm"])
                result["context"] += ltm_text + "\n"
                result["metadata"]["ltm_count"] = len(memories["ltm"])
            
            if context_type in ["rag", "all"]:
                rag_chunks = await self.rag_handler.retrieve_relevant_chunks(
                    user_id, server_id, query, k=5
                )
                rag_text = self.prompt_builder._build_rag_section(rag_chunks)
                result["context"] += rag_text
                result["metadata"]["rag_count"] = len(rag_chunks)
            
            result["metadata"]["tokens"] = self.prompt_builder.estimate_tokens(result["context"])
            logger.debug(f"Focused context prepared: {result['metadata']}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting focused context: {str(e)}")
            return result
    
    async def build_qa_prompt(self, user_id: int, server_id: int, question: str,
                             instructions: str = "", context_type: str = "optimized") -> str:
        """Build complete Q&A prompt with context
        
        Args:
            user_id: User ID
            server_id: Server ID
            question: User question
            instructions: Custom instructions
            context_type: "optimized", "focused", "stm", "ltm", "rag"
            
        Returns:
            Complete prompt ready for LLM
        """
        logger.debug(f"Building Q&A prompt: context_type={context_type}")
        
        try:
            if context_type == "optimized":
                ctx = await self.get_optimized_context(user_id, server_id, question)
                context = ctx["context"]
            else:
                ctx = await self.get_focused_context(user_id, server_id, question, context_type)
                context = ctx["context"]
            
            prompt = self.prompt_builder.build_qa_prompt(question, context, instructions)
            logger.debug(f"Q&A prompt built: {len(prompt)} chars")
            return prompt
            
        except Exception as e:
            logger.error(f"Error building Q&A prompt: {str(e)}")
            return self.prompt_builder.build_qa_prompt(question, "Pas de contexte", instructions)
    
    async def add_to_memory(self, user_id: int, server_id: int, user_message: str,
                           assistant_response: str, document_text: Optional[str] = None) -> Dict:
        """Add interaction to memory (STM, extract LTM, optionally add document)
        
        Args:
            user_id: User ID
            server_id: Server ID
            user_message: User message
            assistant_response: Assistant response
            document_text: Optional document to add to RAG
            
        Returns:
            Metadata about what was added
        """
        logger.debug("Adding to memory")
        
        result = {
            "stm_id": None,
            "ltm_added": 0,
            "document_added": False
        }
        
        try:
            # Add to STM
            combined = f"User: {user_message}\nAssistant: {assistant_response}"
            stm_id = await self.memory_manager.add_conversation_message(
                user_id, server_id, combined, role="assistant"
            )
            result["stm_id"] = stm_id
            logger.debug(f"Added to STM: {stm_id}")
            
            # Add document if provided
            if document_text:
                doc_id, chunk_count = await self.rag_handler.add_document(
                    user_id, server_id, document_text,
                    f"doc_{datetime.utcnow().timestamp()}"
                )
                result["document_added"] = True
                result["document_id"] = doc_id
                result["chunks_created"] = chunk_count
                logger.debug(f"Added document with {chunk_count} chunks")
            
            logger.info(f"Memory updated: STM={result['stm_id']}, RAG={result.get('document_added', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Error Adding to memory: {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return result
    
    async def get_memory_stats(self, user_id: int, server_id: int) -> Dict:
        """Get memory statistics for a user
        
        Args:
            user_id: User ID
            server_id: Server ID
            
        Returns:
            Memory statistics
        """
        logger.debug("Getting memory stats")
        
        try:
            memories = await self.memory_manager.get_long_term_memories(
                user_id, server_id, limit=100
            )
            
            # Group LTM by category
            by_category = {}
            for mem in memories:
                cat = mem.get("category", "other")
                by_category[cat] = by_category.get(cat, 0) + 1
            
            stats = {
                "ltm_total": len(memories),
                "ltm_by_category": by_category,
                "categories": list(by_category.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Memory stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return {"error": str(e)}


# Global context manager instance
_context_manager: Optional[ContextManager] = None


async def initialize_context_manager(memory_manager: MemoryManager, 
                                     rag_handler: RAGHandler) -> None:
    """Initialize global context manager"""
    global _context_manager
    logger.debug("Initializing global context manager")
    _context_manager = ContextManager(memory_manager, rag_handler)


def get_context_manager() -> ContextManager:
    """Get global context manager
    
    Raises:
        RuntimeError: If not initialized
    """
    global _context_manager
    if _context_manager is None:
        raise RuntimeError("ContextManager not initialized. Call initialize_context_manager() first.")
    return _context_manager
