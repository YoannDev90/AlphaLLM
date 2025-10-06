"""
Module API AlphaLLM
Système d'API REST pour l'interaction avec les modèles IA
"""

import logging
from utils.config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

logger.debug("Module API AlphaLLM initialisé")

__version__ = "1.0.0"
__author__ = "AlphaLLM Team"

__all__ = [
    'api',
    'endpoints',
    'utils'
]