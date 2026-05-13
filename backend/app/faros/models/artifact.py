from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ArtifactRecord(BaseModel):
    """A persistent artifact produced by a capability execution."""

    id: str
    type: str
    uri: str
    producer: str
    summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
