"""Review domain module.

Stable edit surface:
- `app.modules.review.router`
- `app.modules.review.service`
"""

from .router import router
from .service import generate_review

__all__ = ["router", "generate_review"]
