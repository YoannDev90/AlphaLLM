"""Fact Extractor - Structured extraction from conversations for LTM"""

import logging
import json
from typing import List, Dict, Optional, Set
from datetime import datetime
import litellm

logger = logging.getLogger("AlphaLLM.FactExtractor")


class FactTemplate:
    """Generic JSON template for fact extraction"""
    
    # Base schema - adapts to content
    BASE_SCHEMA = {
        "type": "object",
        "properties": {
            "facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Fact identifier/title"},
                        "value": {"type": "string", "description": "Fact content"},
                        "category": {
                            "type": "string",
                            "enum": [
                                "preferences",
                                "skills",
                                "background",
                                "interests",
                                "constraints",
                                "contact",
                                "relationships",
                                "goals",
                                "other"
                            ]
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Confidence score (0-1)"
                        }
                    },
                    "required": ["key", "value", "category"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["facts"],
        "additionalProperties": False
    }
    
    @staticmethod
    def get_schema_string() -> str:
        """Get schema as formatted string for prompts"""
        return json.dumps(FactTemplate.BASE_SCHEMA, indent=2)


class FactExtractor:
    """Extracts structured facts from conversations for LTM storage"""
    
    def __init__(self, model: str = "groq/llama-3.1-8b-instant", temperature: float = 0.1):
        """Initialize fact extractor
        
        Args:
            model: LLM model to use for extraction
            temperature: Temperature for extraction (lower = more consistent)
        """
        self.model = model
        self.temperature = temperature
        self.schema = FactTemplate.BASE_SCHEMA
        logger.debug(f"FactExtractor initialized with model={model}, temperature={temperature}")
    
    def _get_extraction_prompt(self, user_message: str, assistant_response: str) -> str:
        """Build extraction prompt with few-shot examples
        
        Args:
            user_message: User input
            assistant_response: Assistant response
            
        Returns:
            Formatted prompt
        """
        prompt = f"""Tu es un expert en extraction de faits. Analyse cette conversation et extrais UNIQUEMENT les faits objectifs et utiles.

SCHEMA JSON (respecter strictement):
{FactTemplate.get_schema_string()}

EXEMPLES FEW-SHOT:

Exemple 1 - Préférences:
Utilisateur: "J'adore les pizzas avec beaucoup de fromage"
Assistant: "C'est une excellente combinaison!"
Réponse:
{{
  "facts": [
    {{"key": "pizza_preference", "value": "Aime les pizzas avec beaucoup de fromage", "category": "preferences", "confidence": 0.9}}
  ]
}}

Exemple 2 - Compétences:
Utilisateur: "Je maîtrise Python depuis 5 ans et j'ai travaillé avec Django et FastAPI"
Assistant: "C'est une belle expérience en backend!"
Réponse:
{{
  "facts": [
    {{"key": "python_experience", "value": "5 ans d'expérience en Python", "category": "skills", "confidence": 0.95}},
    {{"key": "web_frameworks", "value": "Maîtrise de Django et FastAPI", "category": "skills", "confidence": 0.9}}
  ]
}}

Exemple 3 - Arrière-plan:
Utilisateur: "Je suis ingénieur logiciel à Paris depuis 3 ans"
Assistant: "Super! Paris a une belle tech scene."
Réponse:
{{
  "facts": [
    {{"key": "profession", "value": "Ingénieur logiciel", "category": "background", "confidence": 0.95}},
    {{"key": "location", "value": "Paris", "category": "background", "confidence": 0.9}},
    {{"key": "tenure", "value": "3 ans", "category": "background", "confidence": 0.85}}
  ]
}}

CONVERSATION À ANALYSER:

Utilisateur: {user_message}
Assistant: {assistant_response}

Extraction (JSON):"""
        return prompt
    
    async def extract_facts(self, user_message: str, assistant_response: str) -> List[Dict]:
        """Extract facts from conversation pair
        
        Args:
            user_message: User message
            assistant_response: Assistant response
            
        Returns:
            List of extracted facts
        """
        logger.debug(f"Extracting facts from conversation pair")
        
        try:
            prompt = self._get_extraction_prompt(user_message, assistant_response)
            
            messages = [
                {
                    "role": "system",
                    "content": "Tu es un expert en extraction d'informations. Réponds TOUJOURS avec du JSON valide."
                },
                {"role": "user", "content": prompt}
            ]
            
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=1000,
                timeout=15
            )
            
            extraction_text = response.choices[0].message.content
            logger.debug(f"Raw extraction: {extraction_text[:150]}")
            
            # Parse JSON
            try:
                json_start = extraction_text.find('{')
                json_end = extraction_text.rfind('}') + 1
                if json_start >= 0 and json_end > 0:
                    json_str = extraction_text[json_start:json_end]
                    extracted = json.loads(json_str)
                    facts = extracted.get("facts", [])
                    logger.info(f"Extracted {len(facts)} facts")
                    return facts
                else:
                    logger.warning("No JSON found in response")
                    return []
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing error: {e}")
                return []
        
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return []
    
    async def filter_new_facts(self, existing_facts: List[Dict], new_facts: List[Dict]) -> List[Dict]:
        """Filter new facts to avoid duplicates
        
        Args:
            existing_facts: List of existing LTM facts
            new_facts: List of newly extracted facts
            
        Returns:
            Filtered list of truly new facts
        """
        logger.debug(f"Filtering {len(new_facts)} facts against {len(existing_facts)} existing")
        
        # Build set of existing keys
        existing_keys: Set[str] = {
            fact.get("key", "").lower() for fact in existing_facts
        }
        
        filtered = []
        for fact in new_facts:
            key = fact.get("key", "").lower()
            
            if not key or not fact.get("value"):
                logger.debug(f"Skipping empty fact: {fact}")
                continue
            
            # Check for exact match
            if key in existing_keys:
                logger.debug(f"Duplicate key found: {key}")
                continue
            
            # Check for similar keys (fuzzy match)
            is_similar = any(
                self._similarity_score(key, existing_key) > 0.8
                for existing_key in existing_keys
            )
            
            if is_similar:
                logger.debug(f"Similar key found: {key}")
                continue
            
            filtered.append(fact)
            logger.debug(f"New fact accepted: {key}")
        
        logger.info(f"Filtered to {len(filtered)} new facts")
        return filtered
    
    @staticmethod
    def _similarity_score(s1: str, s2: str) -> float:
        """Calculate string similarity (0-1)
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Similarity score
        """
        # Simple Jaccard similarity
        if not s1 or not s2:
            return 0.0
        
        set1 = set(s1.split())
        set2 = set(s2.split())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    async def validate_fact(self, fact: Dict) -> bool:
        """Validate a fact against schema
        
        Args:
            fact: Fact to validate
            
        Returns:
            True if valid
        """
        required = {"key", "value", "category"}
        
        if not isinstance(fact, dict):
            logger.warning("Fact is not a dictionary")
            return False
        
        # Check required fields
        if not all(field in fact for field in required):
            logger.warning(f"Missing required fields in fact: {fact}")
            return False
        
        # Check category
        valid_categories = {
            "preferences", "skills", "background", "interests",
            "constraints", "contact", "relationships", "goals", "other"
        }
        
        if fact.get("category") not in valid_categories:
            logger.warning(f"Invalid category: {fact.get('category')}")
            return False
        
        # Check confidence if present
        if "confidence" in fact:
            if not isinstance(fact["confidence"], (int, float)) or \
               not (0 <= fact["confidence"] <= 1):
                logger.warning(f"Invalid confidence: {fact.get('confidence')}")
                return False
        
        return True