"""
Fichier d'initialisation pour les endpoints de l'API AlphaLLM
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
import asyncio
import logging
import json
import os

from utils.config import LOGGER_NAME, REQUEST_TIMEOUT
from utils.security import get_api_key, verify_api_access

logger = logging.getLogger(LOGGER_NAME)

# Configuration de la sécurité pour Swagger
bearer_scheme = HTTPBearer(
    scheme_name="API Key",
    description="Entrez votre clé API",
    bearerFormat="API Key"
)

def load_models_data(model_type: str):
    """Charge les données des modèles depuis les fichiers JSON"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "..", "models", f"{model_type}_models.json")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données de modèles {model_type}: {str(e)}")
        return {}