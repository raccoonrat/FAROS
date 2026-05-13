from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProviderTask(BaseModel):
    """Provider invocation request."""

    capability_id: str
    provider: str
    model: Optional[str] = None
    prompt: Optional[str] = None
    messages: List[Dict[str, str]] = Field(default_factory=list)
    options: Dict[str, Any] = Field(default_factory=dict)


class ProviderResult(BaseModel):
    """Provider invocation response."""

    ok: bool
    provider: str
    model: str
    text: str = ""
    usage: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: int = 0
    error: Optional[str] = None
