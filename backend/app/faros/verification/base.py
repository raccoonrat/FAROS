from abc import ABC, abstractmethod

from app.faros.models.capability import CapabilityResult
from app.faros.models.verification import VerificationResult


class BaseVerifier(ABC):
    """Base verifier contract."""

    @abstractmethod
    def verify(self, capability_id: str, result: CapabilityResult) -> VerificationResult:
        raise NotImplementedError
