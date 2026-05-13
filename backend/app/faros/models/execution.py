from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .profile import CapabilityBinding


class ExecutionContext(BaseModel):
    """Runtime context passed into each capability."""

    run_id: str
    blueprint_id: str
    profile_id: str
    node_id: str
    capability_id: str
    provider_bindings: Dict[str, CapabilityBinding] = Field(default_factory=dict)
    memory: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)

    def get_binding(self, capability_id: Optional[str] = None) -> Optional[CapabilityBinding]:
        key = capability_id or self.capability_id
        return self.provider_bindings.get(key)


class StepState(BaseModel):
    """Persistent execution state for one workflow node."""

    node_id: str
    capability: str
    status: str = "pending"
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    outputs_summary: Dict[str, Any] = Field(default_factory=dict)
    verification: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class FarosRunRecord(BaseModel):
    """Top-level run record persisted by the FAROS runtime."""

    id: str
    blueprint_id: str
    profile_id: str
    status: str
    execution_mode: str = "execute"
    created_at: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    steps: List[StepState] = Field(default_factory=list)
    output_summary: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
