from abc import ABC, abstractmethod

from app.faros.models.provider import ProviderResult, ProviderTask


class BaseProvider(ABC):
    """Base provider contract for FAROS execution."""

    provider_type: str

    @abstractmethod
    def invoke(self, task: ProviderTask) -> ProviderResult:
        raise NotImplementedError
