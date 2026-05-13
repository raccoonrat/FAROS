from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .artifact import ArtifactRecord


class CapabilityResult(BaseModel):
    """Normalized output contract for all FAROS capabilities."""

    status: str = "completed"
    outputs: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[ArtifactRecord] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    verification: Dict[str, Any] = Field(default_factory=dict)
