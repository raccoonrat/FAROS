"""Idea domain module.

Stable edit surface:
- `app.modules.idea.router`
- `app.modules.idea.service`
"""

from .router import router
from .service import IdeaGenerationService, get_idea_service

__all__ = ["router", "IdeaGenerationService", "get_idea_service"]
