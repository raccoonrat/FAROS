"""Paper domain module.

Stable edit surface:
- `app.modules.paper.router`
- `app.modules.paper.service`
"""

from .router import router
from .service import generate_paper

__all__ = ["router", "generate_paper"]
