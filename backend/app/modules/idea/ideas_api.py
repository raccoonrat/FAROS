"""
Idea Generation API Endpoints

Provides endpoints for managing idea generation sessions.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from app.modules.idea.contracts import (
    IdeaSession,
    IdeaSessionStatus,
    IdeaSessionConfig,
    IdeaCandidate,
    LiteratureItem,
    WorkflowTrace,
    StepResult,
)
from app.modules.idea.service import get_idea_service
from app.services.plan_builder import build_research_plan_from_candidate, candidate_to_plan_dict
from app.modules.idea.storage import get_plan_storage
from app.core.settings import get_settings
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ideas", tags=["ideas"])


# Request/Response Schemas

class CreateSessionRequest(BaseModel):
    """Request to create an idea generation session."""
    providerName: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    directionId: Optional[str] = None
    seedQuery: str = Field(..., min_length=3)
    paperType: str = Field(default="algorithm", description="Type of paper: algorithm, system, application, benchmark, survey, position, theory, evaluation, reproducibility, safety")
    maxCandidates: int = Field(default=5, ge=1, le=20)
    maxPapers: int = Field(default=10, ge=1, le=50)
    domain: Optional[str] = None
    constraints: Optional[List[str]] = None
    mustCiteList: Optional[List[str]] = None


class SessionResponse(BaseModel):
    """Response for session operations."""
    id: str
    createdAt: str
    status: str
    config: dict
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    duration: Optional[int] = None
    candidateIds: List[str] = []
    selectedCandidateId: Optional[str] = None
    errorMessage: Optional[str] = None


class TraceResponse(BaseModel):
    """Response for session trace."""
    sessionId: str
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    totalSteps: int = 0
    successfulSteps: int = 0
    failedSteps: int = 0
    steps: List[dict] = []


class LiteratureResponse(BaseModel):
    """Response for literature items."""
    items: List[dict]
    total: int


class CandidateResponse(BaseModel):
    """Response for a single candidate."""
    id: str
    sessionId: str
    title: str
    problem: str
    keyInsight: str
    novelty: float
    noveltyRationale: str
    feasibility: float
    feasibilityRationale: str
    impact: float
    impactRationale: str
    clarity: float = 5.0
    clarityRationale: str = ""
    risk: float = 5.0
    riskRationale: str = ""
    alignment: float = 5.0
    alignmentRationale: str = ""
    referenceSupport: float = 5.0
    referenceSupportRationale: str = ""
    experimentSpecificity: float = 5.0
    experimentSpecificityRationale: str = ""
    overallScore: float
    scoreBreakdown: dict = {}
    overallRationale: str = ""
    scoringConfidence: float = 0.5
    scoringMethod: str = "pending"
    risks: List[dict] = []
    requiredExperiments: List[dict] = []
    expectedMetrics: List[str] = []
    draftPlan: Optional[dict] = None
    references: List[str] = []
    createdAt: str


class CandidatesResponse(BaseModel):
    """Response for candidates list."""
    candidates: List[CandidateResponse]
    total: int


class SelectCandidateRequest(BaseModel):
    """Request to select a candidate."""
    candidateId: str


class SelectCandidateResponse(BaseModel):
    """Response after selecting a candidate."""
    ok: bool
    candidateId: str
    planId: str
    plan: dict


class SessionListResponse(BaseModel):
    """Response for listing sessions."""
    sessions: List[SessionResponse]
    total: int


def _session_to_response(session: IdeaSession) -> SessionResponse:
    """Convert session to response format."""
    return SessionResponse(
        id=session.id,
        createdAt=session.createdAt.isoformat() if session.createdAt else "",
        status=session.status.value,
        config=session.config.model_dump(),
        startedAt=session.startedAt.isoformat() if session.startedAt else None,
        endedAt=session.endedAt.isoformat() if session.endedAt else None,
        duration=session.duration,
        candidateIds=session.candidateIds,
        selectedCandidateId=session.selectedCandidateId,
        errorMessage=session.errorMessage,
    )


def _candidate_to_response(candidate: IdeaCandidate) -> CandidateResponse:
    """Convert candidate to response format."""
    return CandidateResponse(
        id=candidate.id,
        sessionId=candidate.sessionId,
        title=candidate.title,
        problem=candidate.problem,
        keyInsight=candidate.keyInsight,
        novelty=candidate.novelty,
        noveltyRationale=candidate.noveltyRationale,
        feasibility=candidate.feasibility,
        feasibilityRationale=candidate.feasibilityRationale,
        impact=candidate.impact,
        impactRationale=candidate.impactRationale,
        clarity=getattr(candidate, 'clarity', 5.0),
        clarityRationale=getattr(candidate, 'clarityRationale', ''),
        risk=getattr(candidate, 'risk', 5.0),
        riskRationale=getattr(candidate, 'riskRationale', ''),
        alignment=getattr(candidate, 'alignment', 5.0),
        alignmentRationale=getattr(candidate, 'alignmentRationale', ''),
        referenceSupport=getattr(candidate, 'referenceSupport', 5.0),
        referenceSupportRationale=getattr(candidate, 'referenceSupportRationale', ''),
        experimentSpecificity=getattr(candidate, 'experimentSpecificity', 5.0),
        experimentSpecificityRationale=getattr(candidate, 'experimentSpecificityRationale', ''),
        overallScore=candidate.overallScore,
        scoreBreakdown=candidate.scoreBreakdown,
        overallRationale=getattr(candidate, 'overallRationale', ''),
        scoringConfidence=getattr(candidate, 'scoringConfidence', 0.5),
        scoringMethod=getattr(candidate, 'scoringMethod', 'pending'),
        risks=[r.model_dump() for r in candidate.risks],
        requiredExperiments=[e.model_dump() for e in candidate.requiredExperiments],
        expectedMetrics=candidate.expectedMetrics,
        draftPlan=candidate.draftPlan.model_dump() if candidate.draftPlan else None,
        references=candidate.references,
        createdAt=candidate.createdAt.isoformat() if candidate.createdAt else "",
    )


# Endpoints

@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Idea Session",
    description="Create a new idea generation session."
)
async def create_session(request: CreateSessionRequest) -> SessionResponse:
    """Create a new idea generation session."""
    service = get_idea_service()
    settings = get_settings()
    provider_name = request.providerName or settings.get_active_provider()
    model_name = request.model or settings.get_active_model(provider_name)
    
    config = IdeaSessionConfig(
        providerName=provider_name,
        model=model_name,
        directionId=request.directionId,
        seedQuery=request.seedQuery,
        paperType=request.paperType,
        maxCandidates=request.maxCandidates,
        maxPapers=request.maxPapers,
        domain=request.domain,
        constraints=request.constraints,
        mustCiteList=request.mustCiteList,
    )
    
    session = service.create_session(config)
    return _session_to_response(session)


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="List Idea Sessions",
    description="List all idea generation sessions."
)
async def list_sessions(status_filter: Optional[str] = None) -> SessionListResponse:
    """List all sessions."""
    service = get_idea_service()
    
    status_enum = None
    if status_filter:
        try:
            status_enum = IdeaSessionStatus(status_filter)
        except ValueError:
            pass
    
    sessions = service.list_sessions(status_enum)
    return SessionListResponse(
        sessions=[_session_to_response(s) for s in sessions],
        total=len(sessions),
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get Idea Session",
    description="Get an idea generation session by ID."
)
async def get_session(session_id: str) -> SessionResponse:
    """Get session by ID."""
    service = get_idea_service()
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return _session_to_response(session)


@router.post(
    "/sessions/{session_id}/start",
    response_model=SessionResponse,
    summary="Start Idea Session",
    description="Start an idea generation session and run the pipeline."
)
async def start_session(
    session_id: str,
    background_tasks: BackgroundTasks
) -> SessionResponse:
    """Start a session and run pipeline in background."""
    service = get_idea_service()
    
    try:
        session = service.start_session(session_id)
        
        # Run pipeline in background
        background_tasks.add_task(service.run_pipeline, session_id)
        
        return _session_to_response(session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/sessions/{session_id}/cancel",
    response_model=SessionResponse,
    summary="Cancel Idea Session",
    description="Cancel a running idea generation session."
)
async def cancel_session(session_id: str) -> SessionResponse:
    """Cancel a session."""
    service = get_idea_service()
    
    try:
        session = service.cancel_session(session_id)
        return _session_to_response(session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/sessions/{session_id}/trace",
    response_model=TraceResponse,
    summary="Get Session Trace",
    description="Get the workflow trace for a session."
)
async def get_session_trace(session_id: str) -> TraceResponse:
    """Get session trace."""
    service = get_idea_service()
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
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
                "name": s.name,
                "status": s.status,
                "inputs": s.inputs,
                "outputs": s.outputs,
                "artifacts": s.artifacts,
                "startedAt": s.startedAt.isoformat() if s.startedAt else None,
                "endedAt": s.endedAt.isoformat() if s.endedAt else None,
                "durationSeconds": s.durationSeconds,
                "error": s.error,
            }
            for s in trace.steps
        ],
    )


@router.get(
    "/sessions/{session_id}/literature",
    response_model=LiteratureResponse,
    summary="Get Session Literature",
    description="Get literature items for a session."
)
async def get_session_literature(session_id: str) -> LiteratureResponse:
    """Get literature items for a session."""
    service = get_idea_service()
    
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    items = service.get_literature(session_id)
    return LiteratureResponse(
        items=[
            {
                "id": item.id,
                "sessionId": item.sessionId,
                "title": item.title,
                "authors": item.authors,
                "venue": item.venue,
                "year": item.year,
                "url": item.url,
                "doi": item.doi,
                "arxivId": item.arxivId,
                "snippet": item.snippet,
                "relevanceScore": item.relevanceScore,
                "source": item.source,
                "createdAt": item.createdAt.isoformat() if item.createdAt else "",
            }
            for item in items
        ],
        total=len(items),
    )


@router.get(
    "/sessions/{session_id}/candidates",
    response_model=CandidatesResponse,
    summary="Get Session Candidates",
    description="Get candidate ideas for a session."
)
async def get_session_candidates(session_id: str) -> CandidatesResponse:
    """Get candidates for a session."""
    service = get_idea_service()
    
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    candidates = service.get_candidates(session_id)
    return CandidatesResponse(
        candidates=[_candidate_to_response(c) for c in candidates],
        total=len(candidates),
    )


@router.post(
    "/sessions/{session_id}/select",
    response_model=SelectCandidateResponse,
    summary="Select Candidate",
    description="Select a candidate and create a ResearchPlan from it."
)
async def select_candidate(
    session_id: str,
    request: SelectCandidateRequest
) -> SelectCandidateResponse:
    """Select a candidate and create a ResearchPlan."""
    service = get_idea_service()
    
    # Get session
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Check session is completed
    if session.status != IdeaSessionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session must be completed before selecting. Current status: {session.status.value}"
        )
    
    # Check if already selected (idempotent - return existing)
    if session.selectedCandidateId == request.candidateId:
        # Already selected this candidate, return existing plan info
        plan_storage = get_plan_storage()
        # Try to find existing plan by source_candidate_id
        existing_plans = plan_storage.list_all()
        for plan in existing_plans:
            if hasattr(plan, 'source_candidate_id') and plan.source_candidate_id == request.candidateId:
                return SelectCandidateResponse(
                    ok=True,
                    candidateId=request.candidateId,
                    planId=plan.id,
                    plan={
                        "id": plan.id,
                        "source_session_id": getattr(plan, 'source_session_id', session_id),
                        "source_candidate_id": request.candidateId,
                        "source_candidate_index": getattr(plan, 'source_candidate_index', None),
                        "source_title": getattr(plan, 'source_title', None),
                    },
                )
    
    # Get candidate and determine its index
    candidates = service.get_candidates(session_id)
    candidate = None
    candidate_index = 0
    for idx, c in enumerate(candidates, start=1):
        if c.id == request.candidateId:
            candidate = c
            candidate_index = idx
            break
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {request.candidateId} not found in session {session_id}"
        )
    
    # Build ResearchPlan from candidate using plan builder
    try:
        plan = build_research_plan_from_candidate(
            candidate=candidate,
            seed_query=session.config.seedQuery,
            paper_type=session.config.paperType,
            session_id=session_id,
            candidate_index=candidate_index,
            direction_id=session.config.directionId,
        )
    except ValidationError as e:
        logger.error(f"Failed to build plan from candidate: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to create valid research plan: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error building plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error creating plan: {str(e)}"
        )
    
    # Save plan to storage
    plan_storage = get_plan_storage()
    try:
        created_plan = plan_storage.create(plan)
    except Exception as e:
        logger.error(f"Failed to save plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save research plan: {str(e)}"
        )
    
    # Update session with selection
    service.select_candidate(session_id, request.candidateId)
    
    # Build response
    plan_dict = candidate_to_plan_dict(
        candidate=candidate,
        seed_query=session.config.seedQuery,
        paper_type=session.config.paperType,
        session_id=session_id,
        candidate_index=candidate_index,
        direction_id=session.config.directionId,
    )
    plan_dict["id"] = created_plan.id
    plan_dict["source_session_id"] = session_id
    plan_dict["source_candidate_id"] = candidate.id
    plan_dict["source_candidate_index"] = candidate_index
    plan_dict["source_title"] = candidate.title
    
    return SelectCandidateResponse(
        ok=True,
        candidateId=request.candidateId,
        planId=created_plan.id,
        plan=plan_dict,
    )
