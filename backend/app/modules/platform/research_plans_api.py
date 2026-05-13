"""Platform-owned research plans API implementation."""

from fastapi import APIRouter, HTTPException, status

from app.modules.platform.contracts import ResearchPlanCreate, ResearchPlanResponse
from app.schemas.research_plan import ResearchPlanListResponse
from app.services.research_plan_service import get_service

router = APIRouter(prefix="/research/plans", tags=["research_plans"])


@router.post("", response_model=ResearchPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_research_plan(plan_data: ResearchPlanCreate) -> ResearchPlanResponse:
    service = get_service()
    try:
        plan = service.create_plan(plan_data)
        return ResearchPlanResponse.model_validate(plan)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create research plan: {str(exc)}",
        )


@router.get("/{plan_id}", response_model=ResearchPlanResponse)
async def get_research_plan(plan_id: str) -> ResearchPlanResponse:
    service = get_service()
    plan = service.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchPlan with id '{plan_id}' not found",
        )
    return ResearchPlanResponse.model_validate(plan)


@router.get("", response_model=ResearchPlanListResponse)
async def list_research_plans() -> ResearchPlanListResponse:
    service = get_service()
    plans = service.list_plans()
    return ResearchPlanListResponse(
        plans=[ResearchPlanResponse.model_validate(p) for p in plans],
        total=len(plans),
    )
