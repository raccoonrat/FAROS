"""Idea module router.

This wrapper defines the stable import path for idea HTTP endpoints while the
module-owned `app.modules.idea.ideas_api` implementation is the primary entrypoint.
"""

from fastapi import APIRouter

from app.modules.idea.ideas_api import router as ideas_router

router = APIRouter(tags=["module:idea"])
router.include_router(ideas_router)
