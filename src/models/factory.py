#!/usr/bin/env python3
"""
Model factory for Fama AI.

This module provides a factory for creating models with different providers.
"""
import os
import logging
from typing import Dict, Any, Optional, Union

from agno.models.base import Model
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
from models.formation import Formation

# Set up logging
logger = logging.getLogger(__name__)

# Available model providers
PROVIDERS = {
    "formation": Formation,
    "openai": OpenAIChat,
    "anthropic": Claude,
}

def create_model(
    provider: str = "formation",
    model_id: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs: Any
) -> Model:
    """
    Create a model instance with the specified provider.

    Args:
        provider: The model provider (formation, openai, anthropic)
        model_id: The model ID (if None, will use default for provider)
        temperature: The temperature to use for generation
        max_tokens: The maximum number of tokens to generate
        **kwargs: Additional keyword arguments for the model

    Returns:
        Model: An instance of the specified model

    Raises:
        ValueError: If the provider is not supported
    """
    # Default to Formation if not specified
    provider = provider.lower()

    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported model provider: {provider}. Available providers: {', '.join(PROVIDERS.keys())}")

    model_class = PROVIDERS[provider]

    # Get default model ID for provider if not specified
    if model_id is None:
        if provider == "formation":
            model_id = "best-quality"
        elif provider == "openai":
            model_id = "gpt-4o"
        elif provider == "anthropic":
            model_id = "claude-3-opus-20240229"

    # Get API key from environment variables if not in kwargs
    if "api_key" not in kwargs:
        if provider == "formation":
            api_key = os.environ.get("FORMATION_API_KEY")
        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
        elif provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")

        if api_key:
            kwargs["api_key"] = api_key

    # Create model instance
    model_params = {
        "id": model_id,
        **kwargs
    }

    if temperature is not None:
        model_params["temperature"] = temperature

    if max_tokens is not None:
        model_params["max_tokens"] = max_tokens

    logger.info(f"Creating {provider} model with ID: {model_id}")
    return model_class(**model_params) 
