from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CapabilityBinding(BaseModel):
    """Maps one capability to a concrete provider implementation."""

    provider_type: str = "llm"
    provider: str
    model: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class Profile(BaseModel):
    """Execution profile for a blueprint."""

    id: str
    name: str
    version: str
    description: str = ""
    capability_bindings: Dict[str, CapabilityBinding] = Field(default_factory=dict)
    defaults: Dict[str, Any] = Field(default_factory=dict)
    verification_policy: Dict[str, Any] = Field(default_factory=dict)
