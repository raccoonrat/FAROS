"""Paper module router."""

from fastapi import APIRouter

from app.modules.paper.papers_api import router as papers_router

router = APIRouter(tags=["module:paper"])
router.include_router(papers_router)
