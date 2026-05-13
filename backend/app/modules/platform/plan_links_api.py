"""Platform-owned plan-links API implementation."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.modules.platform.storage import create_plan_link, get_plan_link_context

router = APIRouter(prefix="/code/plan-links", tags=["plan_links"])


class PlanLinkCreate(BaseModel):
    planSessionId: str
    candidateId: str
    candidateIndex: Optional[int] = None


class PlanLinkResponse(BaseModel):
    linkId: str
    planSessionId: str
    candidateId: str
    candidateIndex: Optional[int] = None
    createdAt: str


class PlanContextResponse(BaseModel):
    linkId: str
    planSessionId: str
    candidateId: str
    candidateIndex: Optional[int] = None
    session: Optional[Dict[str, Any]] = None
    candidate: Optional[Dict[str, Any]] = None
    createdAt: str


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PlanLinkResponse)
async def create_plan_link_endpoint(body: PlanLinkCreate):
    record = create_plan_link(
        plan_session_id=body.planSessionId,
        candidate_id=body.candidateId,
        candidate_index=body.candidateIndex,
    )
    return PlanLinkResponse(**record)


@router.get("/{link_id}", response_model=PlanContextResponse)
async def get_plan_link_endpoint(link_id: str):
    context = get_plan_link_context(link_id)
    if not context:
        raise HTTPException(status_code=404, detail=f"Plan link {link_id} not found")
    return PlanContextResponse(**context)
