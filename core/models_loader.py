"""Load model and provider definitions for LiteLLM integration."""

import json
import os
import time
from typing import Dict, List, Optional

from core.config import cfg
from utils.logger import get_logger

logger = get_logger()


class Provider:
    """Provider configuration resolved from environment variables.

    Attributes
    ----------
    provider : str
        Provider name.
    env_key : str
        Environment variable that stores the API key.
    api_base : str
        Base URL for the provider API.
    api_key : Optional[str]
        Loaded API key value or None.
    """

    def __init__(self, provider: str, env_key: str, api_base: str):
        """Create a provider configuration wrapper.

        Parameters
        ----------
        provider : str
            Provider name.
        env_key : str
            Environment variable containing the API key.
        api_base : str
            Provider base URL.
        """
        self.provider = provider
        self.env_key = env_key
        self.api_base = api_base
        self.api_key = os.getenv(env_key)
        logger.debug(
            "Provider %s initialized (api_key: %s)",
            provider,
            "Set" if self.api_key else "Missing",
        )

    def __str__(self):
        return self.provider


class Model:
    """A model entry mapped to a provider configuration.

    Attributes
    ----------
    id : str
        Model identifier.
    litellm_id : str
        LiteLLM-compatible model name.
    provider : Provider
        Provider backing this model.
    api_base : str
        Provider base URL.
    api_key : Optional[str]
        Loaded API key value or None.
    """

    def __init__(self, model_id: str, provider: Provider):
        """Create a model entry for a provider.

        Parameters
        ----------
        model_id : str
            Model identifier.
        provider : Provider
            Provider configuration for the model.
        """
        self.id = model_id
        self.litellm_id = f"openai/{model_id}"
        self.provider = provider
        self.api_base = provider.api_base
        self.api_key = provider.api_key

    def __str__(self):
        return f"litellm_id: {self.litellm_id}, provider: {self.provider}, api_key: {self.api_key[10:]}"


def get_model_catalog() -> List[Dict[str, str]]:
    """Return the model catalog with provider metadata.

    Returns
    -------
    List[Dict[str, str]]
        Catalog entries for configured models.
    """
    providers = _load_providers()
    if not os.path.exists(cfg.MODELS_PATH):
        logger.error("Models file not found: %s", cfg.MODELS_PATH)
        return []

    with open(cfg.MODELS_PATH, "r", encoding="utf-8") as f:
        models_data = json.load(f)

    catalog = []
    for m_id in models_data:
        parts = m_id.split("/", 1)
        if len(parts) == 2:
            prov_name = parts[0].lower()
            model_name = parts[1]

            # Strip redundant provider name if present at start of model_name
            if model_name.lower().startswith(f"{prov_name}/"):
                model_name = model_name[len(prov_name) + 1 :]

            provider = providers.get(prov_name)

            catalog.append(
                {
                    "provider": prov_name,
                    "model": model_name,
                    "litellm_id": f"openai/{model_name}",
                    "api_base": provider.api_base if provider else "",
                    "api_key_set": bool(provider and provider.api_key),
                }
            )

    return catalog


def _load_providers() -> Dict[str, Provider]:
    """Load provider configurations from the providers JSON file.

    Returns
    -------
    Dict[str, Provider]
        Providers indexed by lower-case provider name.
    """
    if not os.path.exists(cfg.PROVIDERS_PATH):
        logger.error("Providers file not found: %s", cfg.PROVIDERS_PATH)
        return {}

    with open(cfg.PROVIDERS_PATH, "r", encoding="utf-8") as f:
        providers_list = json.load(f)

    providers = {}
    for p in providers_list:
        name = p.get("provider", "").lower()
        if name:
            providers[name] = Provider(
                p.get("provider"), p.get("env_key"), p.get("api_base")
            )
    return providers


def get_models() -> List[Model]:
    """Return the list of models with available API keys.

    Returns
    -------
    List[Model]
        Models that can be used for generation.
    """
    providers = _load_providers()
    if not os.path.exists(cfg.MODELS_PATH):
        logger.error("Models file not found: %s", cfg.MODELS_PATH)
        return []

    with open(cfg.MODELS_PATH, "r", encoding="utf-8") as f:
        models_data = json.load(f)

    models = []
    for m_id in models_data:
        parts = m_id.split("/", 1)
        if len(parts) == 2:
            prov_name = parts[0].lower()
            model_name = parts[1]

            # Strip redundant provider name if present at start of model_name
            if model_name.lower().startswith(f"{prov_name}/"):
                model_name = model_name[len(prov_name) + 1 :]

            if prov_name in providers and providers[prov_name].api_key:
                models.append(Model(model_name, providers[prov_name]))

    logger.debug("Loaded %d models with valid API keys", len(models))
    return models
