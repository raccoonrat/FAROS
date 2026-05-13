from typing import Dict, List

from app.faros.providers.base import BaseProvider
from app.faros.providers.llm_provider import LLMProvider


class ProviderRegistry:
    """Registry of provider implementations available to FAROS."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}

    def register(self, provider_type: str, provider: BaseProvider) -> None:
        self._providers[provider_type] = provider

    def get(self, provider_type: str) -> BaseProvider:
        if provider_type not in self._providers:
            raise KeyError(f"Provider type '{provider_type}' is not registered")
        return self._providers[provider_type]

    def list(self) -> List[dict]:
        return [{"type": key} for key in sorted(self._providers.keys())]


_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
        _registry.register("llm", LLMProvider())
    return _registry
