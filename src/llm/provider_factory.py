import logging
import os
from pathlib import Path
from typing import Any

import yaml

from src.llm.base import BaseLLMClient
from src.llm.claude_client import ClaudeClient
from src.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_CONFIG_PATH = PROJECT_ROOT / "config" / "model_config.yaml"

PROVIDER_REGISTRY: dict[str, type[BaseLLMClient]] = {
    "claude": ClaudeClient,
    "gemini": GeminiClient,
}


def get_provider_name() -> str:
    """Determine the active LLM provider name from config or environment variable.

    The LLM_PROVIDER environment variable takes precedence over the default
    specified in config/model_config.yaml.

    Args:
        None.

    Returns:
        The provider name as a string (e.g. "claude", "glm").

    Raises:
        ValueError: If the resolved provider is not found in the registry.
    """
    env_provider = os.environ.get("LLM_PROVIDER")
    if env_provider:
        provider_name = env_provider
    else:
        with open(MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg: dict[str, Any] = yaml.safe_load(f)
        provider_name = cfg.get("default_provider", "claude")

    if provider_name not in PROVIDER_REGISTRY:
        available = ", ".join(PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown provider '{provider_name}'. Available providers: {available}"
        )

    logger.info("Using LLM provider: %s", provider_name)
    return provider_name


def create_llm_client(provider_name: str | None = None) -> BaseLLMClient:
    """Create an LLM client instance for the specified (or default) provider.

    Args:
        provider_name: The provider to instantiate. If None, resolves via
            get_provider_name() using config and environment.

    Returns:
        An instance of a BaseLLMClient subclass.

    Raises:
        ValueError: If the provider name is not in the registry.
    """
    if provider_name is None:
        provider_name = get_provider_name()

    if provider_name not in PROVIDER_REGISTRY:
        available = ", ".join(PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown provider '{provider_name}'. Available providers: {available}"
        )

    client_cls = PROVIDER_REGISTRY[provider_name]
    return client_cls()
