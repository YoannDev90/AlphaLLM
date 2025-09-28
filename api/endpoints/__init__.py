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
from api.utils.security_utils import get_api_key, verify_api_access, bearer_scheme
from api.utils.models_utils import load_models_data

logger = logging.getLogger(LOGGER_NAME)