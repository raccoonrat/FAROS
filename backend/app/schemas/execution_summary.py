"""
Execution Summary Schemas

Scientific Responsibility:
- Define semantic blocks for RunDetail dashboard
- Backend owns interpretation and grouping
- Frontend renders blocks without transformation
"""

from typing import Optional
from pydantic import BaseModel, Field


class StatusStripBlock(BaseModel):
    """
    Top status strip data.
    
    Prominent display of run state and timing.
    """
    status: str = Field(..., description="Run status (completed/running/failed/etc)")
    type: str = Field(..., description="Execution mode (plan/idea)")
    started: str = Field(..., description="Start timestamp (ISO 8601)")
    duration: Optional[int] = Field(None, description="Duration in seconds (if completed)")


class LifecycleBlock(BaseModel):
    """
    Lifecycle timing details.
    
    When execution started, ended, and how long it took.
    """
    started: str = Field(..., description="Start timestamp (ISO 8601)")
    ended: Optional[str] = Field(None, description="End timestamp (ISO 8601, if completed)")
    duration: Optional[int] = Field(None, description="Duration in seconds (if completed)")


class ComputePolicyBlock(BaseModel):
    """
    Compute resources and execution policy.
    
    What model, what parameters, what constraints.
    """
    model: str = Field(..., description="LLM model identifier")
    task_level: str = Field(..., description="Task difficulty level")
    max_iterations: int = Field(..., description="Maximum iteration limit")
    steps: Optional[str] = Field(None, description="Steps completed (e.g., '8/10')")


class ExecutionSummary(BaseModel):
    """
    Semantic dashboard blocks for RunDetail UI.
    
    Backend-computed groupings that frontend renders directly.
    """
    status_strip: StatusStripBlock
    lifecycle: LifecycleBlock
    compute_policy: ComputePolicyBlock
