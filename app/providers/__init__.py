"""
Provider Registry

Central registry for all AI provider implementations.
Provides factory functions to get provider instances.
"""

from typing import Dict, Optional, Type

from .base import BaseProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider

# Provider registry - maps provider names to their classes
PROVIDERS: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    # Future providers will be added here:
    # 'anthropic': AnthropicProvider,
}


def get_provider_class(name: str) -> Optional[Type[BaseProvider]]:
    """
    Get provider class by name.

    Args:
        name: Provider name (e.g., 'openai', 'gemini', 'anthropic')

    Returns:
        Provider class, or None if not found
    """
    return PROVIDERS.get(name.lower())


def get_provider(name: str, api_key: str, **kwargs) -> Optional[BaseProvider]:
    """
    Get an initialized provider instance by name.

    Args:
        name: Provider name (e.g., 'openai', 'gemini', 'anthropic')
        api_key: API key for the provider
        **kwargs: Additional provider-specific arguments

    Returns:
        Initialized provider instance, or None if provider not found

    Example:
        provider = get_provider('openai', api_key='sk-...', timeout=30)
    """
    provider_class = get_provider_class(name)
    if provider_class:
        return provider_class(api_key=api_key, **kwargs)
    return None


def list_providers() -> Dict[str, str]:
    """
    Get list of all registered providers with their display names.

    Returns:
        Dictionary mapping provider names to display names

    Example:
        {'openai': 'OpenAI', 'gemini': 'Google Gemini'}
    """
    result = {}
    for name, provider_class in PROVIDERS.items():
        # Create a temporary instance to get the display name
        # (using dummy API key since we only need the name property)
        try:
            temp_instance = provider_class(api_key="dummy")
            result[name] = temp_instance.name
        except Exception:
            # If instantiation fails, use capitalized name as fallback
            result[name] = name.capitalize()

    return result


__all__ = [
    "BaseProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "PROVIDERS",
    "get_provider_class",
    "get_provider",
    "list_providers",
]
