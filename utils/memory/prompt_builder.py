"""Prompt Builder - Structured prompts with context optimization"""

import logging
from typing import List, Dict, Optional, Tuple
import json

logger = logging.getLogger("AlphaLLM.PromptBuilder")


class StructuredPromptBuilder:
    """Builds structured prompts with optimized context and few-shot examples"""
    
    def __init__(self, use_xml: bool = True, use_compression: bool = True):
        """Initialize prompt builder
        
        Args:
            use_xml: Use XML tags for structure (vs JSON)
            use_compression: Apply context compression
        """
        self.use_xml = use_xml
        self.use_compression = use_compression
        logger.debug(f"PromptBuilder initialized: use_xml={use_xml}, compress={use_compression}")
    
    def build_memory_context(self, stm_messages: List[Dict], ltm_facts: List[Dict],
                            rag_chunks: List[Dict], max_tokens: int = 2000) -> str:
        """Build optimized memory context
        
        Args:
            stm_messages: Short-term memory messages
            ltm_facts: Long-term memory facts
            rag_chunks: RAG retrieved document chunks
            max_tokens: Maximum tokens to use
            
        Returns:
            Formatted context string
        """
        logger.debug(f"Building context: {len(stm_messages)} STM, {len(ltm_facts)} LTM, {len(rag_chunks)} RAG")
        
        sections = []
        
        # Build STM section
        if stm_messages:
            stm_section = self._build_stm_section(stm_messages)
            sections.append(stm_section)
        
        # Build LTM section
        if ltm_facts:
            ltm_section = self._build_ltm_section(ltm_facts)
            sections.append(ltm_section)
        
        # Build RAG section
        if rag_chunks:
            rag_section = self._build_rag_section(rag_chunks)
            sections.append(rag_section)
        
        # Join and compress if needed
        context = "\n\n".join(sections)
        
        if self.use_compression and len(context) > max_tokens * 4:  # rough estimate
            logger.debug("Applying context compression")
            context = self._compress_context(context, max_tokens)
        
        logger.debug(f"Context built: {len(context)} characters")
        return context
    
    def _build_stm_section(self, messages: List[Dict]) -> str:
        """Build STM context section
        
        Args:
            messages: List of STM messages
            
        Returns:
            Formatted STM section
        """
        if not messages:
            return ""
        
        if self.use_xml:
            section = "<conversation_history>\n"
            for msg in messages[-5:]:  # Keep only last 5
                role = msg.get("role", "unknown").upper()
                text = msg.get("text", "")
                section += f"  <message role=\"{role}\">{text}</message>\n"
            section += "</conversation_history>"
        else:
            section = "## Conversation History\n"
            for msg in messages[-5:]:
                role = msg.get("role", "unknown")
                text = msg.get("text", "")
                section += f"- [{role}] {text}\n"
        
        return section
    
    def _build_ltm_section(self, facts: List[Dict]) -> str:
        """Build LTM context section
        
        Args:
            facts: List of LTM facts
            
        Returns:
            Formatted LTM section
        """
        if not facts:
            return ""
        
        # Group by category
        by_category = {}
        for fact in facts:
            cat = fact.get("category", "other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(fact)
        
        if self.use_xml:
            section = "<personal_knowledge>\n"
            for category, cat_facts in by_category.items():
                section += f"  <category name=\"{category}\">\n"
                for fact in cat_facts:
                    key = fact.get("key", "unknown")
                    value = fact.get("value", "")
                    confidence = fact.get("confidence", 1.0)
                    section += f"    <fact key=\"{key}\" confidence=\"{confidence}\">{value}</fact>\n"
                section += "  </category>\n"
            section += "</personal_knowledge>"
        else:
            section = "## Personal Knowledge\n"
            for category, cat_facts in by_category.items():
                section += f"\n### {category.title()}\n"
                for fact in cat_facts:
                    key = fact.get("key", "unknown")
                    value = fact.get("value", "")
                    section += f"- **{key}**: {value}\n"
        
        return section
    
    def _build_rag_section(self, chunks: List[Dict]) -> str:
        """Build RAG documents section
        
        Args:
            chunks: List of RAG chunks
            
        Returns:
            Formatted RAG section
        """
        if not chunks:
            return ""
        
        if self.use_xml:
            section = "<relevant_documents>\n"
            for chunk in chunks[:3]:  # Keep top 3
                doc_id = chunk.get("metadata", {}).get("document_id", "unknown")
                relevance = chunk.get("relevance_score", 0)
                content = chunk.get("content", "")[:500]
                section += f"  <document id=\"{doc_id}\" relevance=\"{relevance:.2f}\">\n"
                section += f"    {content}\n"
                section += "  </document>\n"
            section += "</relevant_documents>"
        else:
            section = "## Relevant Documents\n"
            for chunk in chunks[:3]:
                doc_id = chunk.get("metadata", {}).get("document_id", "unknown")
                relevance = chunk.get("relevance_score", 0)
                content = chunk.get("content", "")[:500]
                section += f"\n### Document {doc_id} (relevance: {relevance:.2f})\n"
                section += f"{content}\n"
        
        return section
    
    def _compress_context(self, context: str, target_tokens: int) -> str:
        """Compress context while preserving key information
        
        Args:
            context: Context to compress
            target_tokens: Target token count
            
        Returns:
            Compressed context
        """
        logger.debug(f"Compressing context to {target_tokens} tokens")
        
        # Simple strategy: extract first and last parts
        lines = context.split('\n')
        if len(lines) <= target_tokens // 10:  # rough estimate
            return context
        
        # Keep headers and key facts, remove some details
        compressed = []
        kept = 0
        target_lines = max(10, target_tokens // 10)
        
        for line in lines:
            if any(marker in line for marker in ['<', '##', '###', '-', '*']):
                compressed.append(line)
                kept += 1
                if kept >= target_lines:
                    break
        
        logger.debug(f"Compressed to {len(compressed)} lines")
        return '\n'.join(compressed)
    
    def build_extraction_prompt(self, conversation: str, examples: int = 3) -> str:
        """Build fact extraction prompt with examples
        
        Args:
            conversation: Conversation to extract from
            examples: Number of few-shot examples
            
        Returns:
            Formatted extraction prompt
        """
        logger.debug(f"Building extraction prompt with {examples} examples")
        
        prompt = """Tu es un expert en extraction d'informations pertinentes.

Analyse cette conversation et extrais les faits objectifs et utiles pour construire un profil utilisateur.

INSTRUCTIONS:
- Extrais UNIQUEMENT les informations explicitement mentionnées
- Ignore les opinions ou suppositions
- Catégorise chaque fait
- Assigne un score de confiance (0-1)

OUTPUT FORMAT (JSON):
{
  "facts": [
    {"key": "...", "value": "...", "category": "...", "confidence": 0.95},
    ...
  ]
}

CATEGORIES: preferences, skills, background, interests, constraints, contact, relationships, goals, other

---
CONVERSATION:
"""
        prompt += conversation
        prompt += "\n\nEXTRACTION:"
        
        return prompt
    
    def build_qa_prompt(self, question: str, context: str, instructions: str = "") -> str:
        """Build Q&A prompt with context and instructions
        
        Args:
            question: User question
            context: Context from memory
            instructions: Custom instructions
            
        Returns:
            Formatted Q&A prompt
        """
        logger.debug("Building Q&A prompt")
        
        if self.use_xml:
            prompt = "<task>\n"
            prompt += "<instructions>\n"
            prompt += "Tu es un assistant intelligent et utile. Utilise le contexte fourni pour répondre.\n"
            if instructions:
                prompt += f"Instructions spéciales:\n{instructions}\n"
            prompt += "</instructions>\n\n"
            
            prompt += "<context>\n"
            prompt += context
            prompt += "\n</context>\n\n"
            
            prompt += "<question>\n"
            prompt += question
            prompt += "\n</question>\n\n"
            
            prompt += "<response>\n"
            prompt += "</response>"
        else:
            prompt = "## Task\n\n"
            prompt += "**Instructions**: Tu es un assistant intelligent. Utilise le contexte fourni.\n"
            if instructions:
                prompt += f"\n**Instructions spéciales**:\n{instructions}\n"
            
            prompt += f"\n## Context\n{context}\n\n"
            prompt += f"## Question\n{question}\n\n"
            prompt += "## Response\n"
        
        return prompt
    
    def build_summarization_prompt(self, text: str, max_length: int = 200) -> str:
        """Build summarization prompt
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
            
        Returns:
            Formatted summarization prompt
        """
        logger.debug(f"Building summarization prompt (max_length={max_length})")
        
        prompt = f"""Résume le texte suivant en maximum {max_length} mots.
Garde les informations essentielles.

TEXTE:
{text}

RÉSUMÉ:"""
        
        return prompt
    
    def build_few_shot_prompt(self, task: str, examples: List[Tuple[str, str]],
                             new_input: str) -> str:
        """Build few-shot prompt with examples
        
        Args:
            task: Task description
            examples: List of (input, output) examples
            new_input: New input to process
            
        Returns:
            Formatted few-shot prompt
        """
        logger.debug(f"Building few-shot prompt with {len(examples)} examples")
        
        prompt = f"**Task**: {task}\n\n"
        
        prompt += "**Examples**:\n"
        for i, (inp, out) in enumerate(examples, 1):
            prompt += f"\nExample {i}:\n"
            prompt += f"Input: {inp}\n"
            prompt += f"Output: {out}\n"
        
        prompt += f"\n**New Input**: {new_input}\n"
        prompt += "**Output**:"
        
        return prompt
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count
        
        Args:
            text: Text to estimate
            
        Returns:
            Approximate token count
        """
        # Rough estimate: ~4 chars per token
        return len(text) // 4


class RoleBasedPromptBuilder(StructuredPromptBuilder):
    """Specialized prompt builder for different roles/domains"""
    
    def __init__(self, role: str = "assistant", **kwargs):
        """Initialize role-based builder
        
        Args:
            role: Role/domain (assistant, teacher, analyst, etc.)
            **kwargs: Arguments for parent class
        """
        super().__init__(**kwargs)
        self.role = role
        logger.debug(f"RoleBasedPromptBuilder initialized with role={role}")
    
    def build_role_prompt(self, task: str, context: str, **role_args) -> str:
        """Build role-specific prompt
        
        Args:
            task: Task description
            context: Context
            **role_args: Role-specific arguments
            
        Returns:
            Formatted prompt
        """
        logger.debug(f"Building {self.role} prompt")
        
        role_prompts = {
            "teacher": self._build_teacher_prompt,
            "analyst": self._build_analyst_prompt,
            "helper": self._build_helper_prompt,
            "researcher": self._build_researcher_prompt,
        }
        
        builder = role_prompts.get(self.role, self._build_generic_prompt)
        return builder(task, context, **role_args)
    
    def _build_teacher_prompt(self, task: str, context: str, **kwargs) -> str:
        """Build educational prompt"""
        return f"""Tu es un excellent professeur. Explique clairement le concept demandé.

CONTEXTE: {context}

TÂCHE: {task}

Explique simplement et progressivement."""
    
    def _build_analyst_prompt(self, task: str, context: str, **kwargs) -> str:
        """Build analytical prompt"""
        return f"""Tu es un analyste expert. Analyse les données et fournis des insights.

DONNÉES: {context}

TÂCHE: {task}

Analyse structurée avec données chiffrées."""
    
    def _build_helper_prompt(self, task: str, context: str, **kwargs) -> str:
        """Build helpful assistant prompt"""
        return f"""Tu es un assistant utile et sympathique. Aide l'utilisateur.

CONTEXTE: {context}

DEMANDE: {task}

Réponse concise et utile."""
    
    def _build_researcher_prompt(self, task: str, context: str, **kwargs) -> str:
        """Build research prompt"""
        return f"""Tu es un chercheur rigoureux. Fournis une analyse basée sur les preuves.

SOURCES: {context}

QUESTION: {task}

Analyse approfondie avec références."""
    
    def _build_generic_prompt(self, task: str, context: str, **kwargs) -> str:
        """Build generic prompt"""
        return f"""CONTEXTE:
{context}

TÂCHE:
{task}

RÉPONSE:"""
