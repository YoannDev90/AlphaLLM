"""
Utilitaires pour les modèles
"""

import json
import os
import logging

from utils.config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

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