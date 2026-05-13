"""Platform-owned plan sessions API implementation."""

import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from app.core.settings import get_settings
from app.modules.platform.contracts import (
    CandidatePlan,
    PAPER_TYPE_LABELS,
    PlanSession,
    PlanSessionConfig,
    PlanSessionStatus,
)
from app.services.plan_generation_service import get_plan_generation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plans", tags=["plans"])


class CreatePlanSessionRequest(BaseModel):
    providerName: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    ideaSessionId: Optional[str] = None
    ideaCandidateId: Optional[str] = None
    ideaCandidateTitle: Optional[str] = None
    ideaSeedQuery: Optional[str] = None
    paperType: str = Field(default="algorithmic_method")
    directionId: Optional[str] = None
    directionTitle: Optional[str] = None
    maxCandidates: int = Field(default=3, ge=1, le=10)
    userNotes: Optional[str] = None


class PlanSessionResponse(BaseModel):
    id: str
    createdAt: str
    status: str
    config: dict
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    duration: Optional[int] = None
    candidateIds: List[str] = []
    selectedCandidateId: Optional[str] = None
    resultingPlanId: Optional[str] = None
    errorMessage: Optional[str] = None


class PlanSessionListResponse(BaseModel):
    sessions: List[PlanSessionResponse]
    total: int


class TraceResponse(BaseModel):
    sessionId: str
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    totalSteps: int = 0
    successfulSteps: int = 0
    failedSteps: int = 0
    steps: List[dict] = []


class CandidatePlanResponse(BaseModel):
    id: str
    sessionId: str
    indexNumber: int
    title: str
    planAbstract: str
    novelty: str
    feasibility: str
    risks: str
    gapAnalysis: str
    method: str
    experimentDesign: dict
    evaluationProtocol: dict
    ablations: List[str]
    baselines: List[str]
    resourcesEstimate: str
    scoreBreakdown: dict
    overallScore: float
    createdAt: str


class CandidatePlansResponse(BaseModel):
    candidates: List[CandidatePlanResponse]
    total: int


class SelectCandidateRequest(BaseModel):
    candidateId: str


class SelectCandidateResponse(BaseModel):
    ok: bool
    candidateId: str
    selectedPlanId: str
    researchPlanId: str


class PaperTypeItem(BaseModel):
    id: str
    label: str


class PaperTypesResponse(BaseModel):
    paperTypes: List[PaperTypeItem]


def _session_to_response(session: PlanSession) -> PlanSessionResponse:
    return PlanSessionResponse(
        id=session.id,
        createdAt=session.createdAt.isoformat() if session.createdAt else "",
        status=session.status.value,
        config=session.config.model_dump(),
        startedAt=session.startedAt.isoformat() if session.startedAt else None,
        endedAt=session.endedAt.isoformat() if session.endedAt else None,
        duration=session.duration,
        candidateIds=session.candidateIds,
        selectedCandidateId=session.selectedCandidateId,
        resultingPlanId=session.resultingPlanId,
        errorMessage=session.errorMessage,
    )


def _candidate_to_response(candidate: CandidatePlan) -> CandidatePlanResponse:
    return CandidatePlanResponse(
        id=candidate.id,
        sessionId=candidate.sessionId,
        indexNumber=candidate.indexNumber,
        title=candidate.title,
        planAbstract=candidate.planAbstract,
        novelty=candidate.novelty,
        feasibility=candidate.feasibility,
        risks=candidate.risks,
        gapAnalysis=candidate.gapAnalysis,
        method=candidate.method,
        experimentDesign=candidate.experimentDesign.model_dump() if hasattr(candidate.experimentDesign, 'model_dump') else candidate.experimentDesign,
        evaluationProtocol=candidate.evaluationProtocol,
        ablations=candidate.ablations,
        baselines=candidate.baselines,
        resourcesEstimate=candidate.resourcesEstimate,
        scoreBreakdown=candidate.scoreBreakdown.model_dump() if hasattr(candidate.scoreBreakdown, 'model_dump') else candidate.scoreBreakdown,
        overallScore=candidate.overallScore,
        createdAt=candidate.createdAt.isoformat() if candidate.createdAt else "",
    )


@router.get('/paper-types', response_model=PaperTypesResponse)
async def list_paper_types() -> PaperTypesResponse:
    items = [PaperTypeItem(id=paper_type.value, label=label) for paper_type, label in PAPER_TYPE_LABELS.items()]
    return PaperTypesResponse(paperTypes=items)


@router.post('/sessions', response_model=PlanSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: CreatePlanSessionRequest) -> PlanSessionResponse:
    service = get_plan_generation_service()
    settings = get_settings()
    provider_name = request.providerName or settings.get_active_provider()
    model_name = request.model or settings.get_active_model(provider_name)
    config = PlanSessionConfig(
        providerName=provider_name,
        model=model_name,
        ideaSessionId=request.ideaSessionId,
        ideaCandidateId=request.ideaCandidateId,
        ideaCandidateTitle=request.ideaCandidateTitle,
        ideaSeedQuery=request.ideaSeedQuery,
        paperType=request.paperType,
        directionId=request.directionId,
        directionTitle=request.directionTitle,
        maxCandidates=request.maxCandidates,
        userNotes=request.userNotes,
    )
    session = service.create_session(config)
    return _session_to_response(session)


@router.get('/sessions', response_model=PlanSessionListResponse)
async def list_sessions() -> PlanSessionListResponse:
    service = get_plan_generation_service()
    sessions = service.list_sessions()
    return PlanSessionListResponse(sessions=[_session_to_response(s) for s in sessions], total=len(sessions))


@router.get('/sessions/{session_id}', response_model=PlanSessionResponse)
async def get_session(session_id: str) -> PlanSessionResponse:
    service = get_plan_generation_service()
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    return _session_to_response(session)


@router.post('/sessions/{session_id}/generate', response_model=PlanSessionResponse)
async def generate_plans(session_id: str, background_tasks: BackgroundTasks) -> PlanSessionResponse:
    service = get_plan_generation_service()
    try:
        session = service.start_session(session_id)
        background_tasks.add_task(service.run_pipeline, session_id)
        return _session_to_response(session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get('/sessions/{session_id}/trace', response_model=TraceResponse)
async def get_session_trace(session_id: str) -> TraceResponse:
    service = get_plan_generation_service()
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")

    trace = session.trace
    if not trace:
        return TraceResponse(sessionId=session_id)

    return TraceResponse(
        sessionId=session_id,
        startedAt=trace.startedAt.isoformat() if trace.startedAt else None,
        endedAt=trace.endedAt.isoformat() if trace.endedAt else None,
        totalSteps=trace.totalSteps,
        successfulSteps=trace.successfulSteps,
        failedSteps=trace.failedSteps,
        steps=[
            {
                'name': step.name,
                'status': step.status,
                'startedAt': step.startedAt.isoformat() if step.startedAt else None,
                'endedAt': step.endedAt.isoformat() if step.endedAt else None,
                'durationSeconds': step.durationSeconds,
                'error': step.error,
            }
            for step in trace.steps
        ],
    )


@router.get('/sessions/{session_id}/candidates', response_model=CandidatePlansResponse)
async def get_session_candidates(session_id: str) -> CandidatePlansResponse:
    service = get_plan_generation_service()
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    candidates = service.get_candidates(session_id)
    return CandidatePlansResponse(candidates=[_candidate_to_response(c) for c in candidates], total=len(candidates))


@router.post('/sessions/{session_id}/select', response_model=SelectCandidateResponse)
async def select_candidate(session_id: str, request: SelectCandidateRequest) -> SelectCandidateResponse:
    service = get_plan_generation_service()
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if session.status != PlanSessionStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Session must be completed. Current: {session.status.value}")
    if session.selectedCandidateId == request.candidateId and session.resultingPlanId:
        return SelectCandidateResponse(ok=True, candidateId=request.candidateId, selectedPlanId="", researchPlanId=session.resultingPlanId)
    try:
        result = service.select_candidate(session_id, request.candidateId)
        return SelectCandidateResponse(
            ok=True,
            candidateId=request.candidateId,
            selectedPlanId=result['selectedPlanId'],
            researchPlanId=result['researchPlanId'],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Select candidate failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
