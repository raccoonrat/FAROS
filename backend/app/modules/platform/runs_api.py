"""Platform-owned runs API implementation."""

from datetime import datetime as dt
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.modules.platform.contracts import (
    ArtifactResponse,
    ExecutionSummary,
    RunConfig,
    RunCreate,
    RunListResponse,
    RunResponse,
    RunStatus,
    RunType,
    RunUpdate,
)
from app.services.agent_executor import get_agent_executor
from app.services.artifact_service import get_service as get_artifact_service
from app.services.run_service import get_service

router = APIRouter(prefix="/runs", tags=["runs"])


def _build_run_response(run, artifact_service) -> RunResponse:
    response_data = run.model_dump()
    response_data["duration"] = run.duration
    artifacts = artifact_service.list_artifacts(runId=run.id)
    response_data["artifacts"] = [ArtifactResponse.model_validate(a) for a in artifacts]
    return RunResponse(**response_data)


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(run_data: RunCreate) -> RunResponse:
    service = get_service()
    try:
        run = service.create_run(run_data)
        response_data = run.model_dump()
        response_data["duration"] = run.duration
        response_data["artifacts"] = []
        return RunResponse(**response_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create run: {str(exc)}",
        )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str) -> RunResponse:
    service = get_service()
    artifact_service = get_artifact_service()
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id '{run_id}' not found",
        )
    return _build_run_response(run, artifact_service)


@router.patch("/{run_id}", response_model=RunResponse)
async def update_run(run_id: str, update_data: RunUpdate) -> RunResponse:
    service = get_service()
    artifact_service = get_artifact_service()
    try:
        run = service.update_run(run_id, update_data)
        return _build_run_response(run, artifact_service)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update run: {str(exc)}",
        )


@router.get("", response_model=RunListResponse)
async def list_runs(
    status: Optional[str] = Query(None, description="Filter by status"),
    planId: Optional[str] = Query(None, description="Filter by planId"),
    search: Optional[str] = Query(None, description="Free text search in config model/workplaceName"),
    dateFrom: Optional[str] = Query(None, description="Filter runs created after this ISO date"),
    dateTo: Optional[str] = Query(None, description="Filter runs created before this ISO date"),
) -> RunListResponse:
    service = get_service()
    status_enum = None
    if status:
        try:
            status_enum = RunStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Must be one of: pending, running, completed, failed, cancelled",
            )

    runs = service.list_runs(status=status_enum, planId=planId)

    if dateFrom:
        try:
            date_from = dt.fromisoformat(dateFrom.replace("Z", "+00:00"))
            runs = [r for r in runs if r.createdAt >= date_from]
        except (ValueError, TypeError):
            pass

    if dateTo:
        try:
            date_to = dt.fromisoformat(dateTo.replace("Z", "+00:00"))
            runs = [r for r in runs if r.createdAt <= date_to]
        except (ValueError, TypeError):
            pass

    if search:
        search_lower = search.lower()
        filtered = []
        for run in runs:
            config_dict = run.config.model_dump() if run.config else {}
            searchable = " ".join(str(v) for v in config_dict.values() if v).lower()
            if search_lower in searchable or search_lower in (run.planId or "").lower():
                filtered.append(run)
        runs = filtered

    artifact_service = get_artifact_service()
    run_responses = [_build_run_response(run, artifact_service) for run in runs]
    return RunListResponse(runs=run_responses, total=len(run_responses))


@router.post("/{run_id}/start", response_model=RunResponse)
async def start_run(run_id: str, background_tasks: BackgroundTasks) -> RunResponse:
    service = get_service()
    artifact_service = get_artifact_service()
    try:
        executor = get_agent_executor()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Agent executor not available: {str(exc)}. Check that LLM_API_KEY is configured.",
        )

    try:
        run = service.start_run(run_id)
        background_tasks.add_task(executor.execute_run, run_id)
        return _build_run_response(run, artifact_service)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start run: {str(exc)}",
        )


@router.post("/{run_id}/complete", response_model=RunResponse)
async def complete_run(run_id: str, artifactIds: Optional[List[str]] = None) -> RunResponse:
    service = get_service()
    artifact_service = get_artifact_service()
    try:
        run = service.complete_run(run_id, artifactIds=artifactIds)
        return _build_run_response(run, artifact_service)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{run_id}/fail", response_model=RunResponse)
async def fail_run(run_id: str, error_message: str) -> RunResponse:
    service = get_service()
    artifact_service = get_artifact_service()
    try:
        run = service.fail_run(run_id, error_message)
        return _build_run_response(run, artifact_service)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(run_id: str) -> RunResponse:
    service = get_service()
    artifact_service = get_artifact_service()
    try:
        run = service.cancel_run(run_id)
        return _build_run_response(run, artifact_service)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/mock", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_mock_run(planId: Optional[str] = None, notes: Optional[str] = None) -> RunResponse:
    service = get_service()
    mock_config = RunConfig(
        model="mock-model",
        maxIterTimes=1,
        taskLevel="mock",
        workplaceName="mock_workspace",
        cachePath="cache",
        port=8000,
        ideas=notes or "Mock run for testing",
    )
    run_data = RunCreate(
        planId=planId,
        type=RunType.PLAN if planId else RunType.IDEA,
        config=mock_config,
        isMock=True,
    )
    try:
        run = service.create_run(run_data)
        response_data = run.model_dump()
        response_data["duration"] = run.duration
        response_data["artifacts"] = []
        return RunResponse(**response_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{run_id}/execution-summary", response_model=ExecutionSummary)
async def get_execution_summary(run_id: str) -> ExecutionSummary:
    service = get_service()
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id '{run_id}' not found",
        )
    return service.get_execution_summary(run)
