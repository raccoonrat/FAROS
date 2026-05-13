"""Idea-domain storage facade.

This isolates idea-domain callers from the current shared storage layout.
"""

from app.storage.idea_storage import (
    generate_candidate_id,
    generate_literature_id,
    generate_session_id,
    get_candidate_storage,
    get_literature_storage,
    get_session_storage,
)
from app.storage.research_plan_storage import get_storage as get_plan_storage

__all__ = [
    "generate_candidate_id",
    "generate_literature_id",
    "generate_session_id",
    "get_candidate_storage",
    "get_literature_storage",
    "get_plan_storage",
    "get_session_storage",
]
