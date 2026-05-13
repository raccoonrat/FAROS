from typing import Any, Dict

from pydantic import BaseModel, Field


class VerificationResult(BaseModel):
    """Verification result for one capability output."""

    rule_id: str
    status: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
