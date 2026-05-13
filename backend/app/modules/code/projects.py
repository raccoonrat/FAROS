"""Minimal code-module project/service facade."""

from app.services import code_project_service
from app.services.code_agent_service import generate_project_from_plan, get_generation_status

__all__ = [
    "code_project_service",
    "generate_project_from_plan",
    "get_generation_status",
]
