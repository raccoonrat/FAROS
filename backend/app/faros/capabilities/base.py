from abc import ABC, abstractmethod
from typing import Any, Dict

from app.faros.models.capability import CapabilityResult
from app.faros.models.execution import ExecutionContext


class BaseCapability(ABC):
    """Base contract for all FAROS capabilities."""

    capability_id: str
    description: str = ""

    @abstractmethod
    def execute(self, context: ExecutionContext, inputs: Dict[str, Any]) -> CapabilityResult:
        raise NotImplementedError
