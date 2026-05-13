"""Review module router."""

from fastapi import APIRouter

from app.modules.review.reviews_api import router as reviews_router

router = APIRouter(tags=["module:review"])
router.include_router(reviews_router)
