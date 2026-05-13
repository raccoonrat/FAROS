"""
Reviews API — Paper review generation and feedback loop.

Endpoints:
- POST /reviews              (create + generate review for a paper)
- GET  /reviews?paperId=     (list reviews)
- GET  /reviews/{id}         (get review detail)
- POST /reviews/{id}/apply   (apply selected action items as improvement requests)
- GET  /reviews/requests     (list improvement requests)
"""

import logging
import threading
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.settings import get_settings
from app.modules.review.storage import (
    create_review as _create_review, get_review as _get_review,
    list_reviews as _list_reviews, update_review as _update_review,
    create_improvement_request, list_improvement_requests as _list_improvement_requests,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


class CreateReviewRequest(BaseModel):
    paperId: str
    reviewerProfile: str = "senior_reviewer"
    providerName: Optional[str] = None
    model: Optional[str] = None


class ApplyFeedbackRequest(BaseModel):
    actionItemIndices: List[int] = Field(..., description="0-based indices of action items to apply")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_review_endpoint(req: CreateReviewRequest):
    """Create a review and immediately start generation in background."""
    from app.modules.review.storage import get_paper
    paper = get_paper(req.paperId)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper '{req.paperId}' not found")

    settings = get_settings()
    provider_name = req.providerName or settings.get_active_provider()
    model = req.model or settings.get_active_model(provider_name)
    record = _create_review(req.model_dump() | {"providerName": provider_name, "model": model})

    def _run():
        try:
            from app.modules.review.service import generate_review
            generate_review(record["id"])
        except Exception as e:
            logger.error(f"Review generation failed: {e}", exc_info=True)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return record


@router.get("")
async def list_reviews_endpoint(paperId: Optional[str] = None):
    reviews = _list_reviews(paper_id=paperId)
    return {"reviews": reviews, "total": len(reviews)}


@router.get("/requests")
async def list_improvement_requests_endpoint(
    reviewId: Optional[str] = None,
    paperId: Optional[str] = None,
    targetModule: Optional[str] = None,
):
    requests = _list_improvement_requests(
        review_id=reviewId, paper_id=paperId, target_module=targetModule,
    )
    return {"requests": requests, "total": len(requests)}


@router.get("/{review_id}")
async def get_review_endpoint(review_id: str):
    record = _get_review(review_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Review '{review_id}' not found")
    return record


@router.post("/{review_id}/apply")
async def apply_feedback_endpoint(review_id: str, req: ApplyFeedbackRequest):
    """Apply selected action items as improvement requests for target modules."""
    review = _get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail=f"Review '{review_id}' not found")
    if review.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Review not completed yet")

    action_items = review.get("actionItems", [])
    if not action_items:
        raise HTTPException(status_code=400, detail="No action items in review")

    created = []
    for idx in req.actionItemIndices:
        if idx < 0 or idx >= len(action_items):
            continue
        item = action_items[idx]
        ir = create_improvement_request({
            "reviewId": review_id,
            "paperId": review.get("paperId"),
            "targetModule": item.get("targetModule", "papers"),
            "actionItemIndex": idx,
            "description": item.get("description", ""),
            "severity": item.get("severity", "MAJOR"),
            "sectionPointer": item.get("section", ""),
            "suggestedEdit": item.get("suggestedEdit", ""),
        })
        created.append(ir)

    return {
        "reviewId": review_id,
        "appliedCount": len(created),
        "requests": created,
    }
