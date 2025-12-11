"""Utilities for loading model metadata for the API."""
import json
from pathlib import Path
from typing import Any, Dict
from config import LOGGER_NAME
import logging

logger = logging.getLogger(LOGGER_NAME)


def load_models_data(model_type: str) -> Dict[str, Any]:
    """Load the JSON description for a given model type."""
    models_dir = Path(__file__).resolve().parents[1] / "models"
    metadata_path = models_dir / f"{model_type}_models.json"

    if not metadata_path.exists():
        logger.warning(f"Modèle {model_type} introuvable ({metadata_path})")
        return {}

    try:
        with metadata_path.open("r", encoding="utf-8") as metadata_file:
            return json.load(metadata_file)
    except json.JSONDecodeError as exc:
        logger.error(f"JSON invalide dans {metadata_path} : {exc}")
    except Exception as exc:
        logger.error(f"Impossible de lire {metadata_path} : {exc}")

    return {}
