import threading
from typing import Any, Dict, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.faros.registry.blueprint_registry import get_blueprint_registry
from app.faros.registry.capability_registry import get_capability_registry
from app.faros.registry.profile_registry import get_profile_registry
from app.faros.registry.provider_registry import get_provider_registry
from app.faros.runtime.orchestrator import get_orchestrator

router = APIRouter(prefix="/faros", tags=["faros"])


class CreateFarosRunRequest(BaseModel):
    blueprintId: str = "ml_paper"
    profileId: str = "faros_llm"
    executionMode: Literal["plan", "execute"] = "execute"
    asyncExecution: bool = True
    inputs: Dict[str, Any] = Field(default_factory=dict)


@router.get("/health")
async def faros_health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "runtime": "faros",
        "blueprints": len(get_blueprint_registry().list()),
        "profiles": len(get_profile_registry().list()),
        "capabilities": len(get_capability_registry().list()),
    }


@router.get("/blueprints")
async def list_blueprints() -> Dict[str, Any]:
    registry = get_blueprint_registry()
    return {"blueprints": [bp.model_dump() for bp in registry.list()]}


@router.get("/profiles")
async def list_profiles() -> Dict[str, Any]:
    registry = get_profile_registry()
    return {"profiles": [profile.model_dump() for profile in registry.list()]}


@router.get("/capabilities")
async def list_capabilities() -> Dict[str, Any]:
    return {
        "capabilities": get_capability_registry().list(),
        "providers": get_provider_registry().list(),
    }


@router.get("/runs")
async def list_runs() -> Dict[str, Any]:
    runs = get_orchestrator().list_runs()
    return {"runs": runs, "total": len(runs)}


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def create_run(req: CreateFarosRunRequest) -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    run = orchestrator.create_run(
        blueprint_id=req.blueprintId,
        profile_id=req.profileId,
        inputs=req.inputs,
        execution_mode=req.executionMode,
    )
    if req.executionMode == "plan":
        return run

    if req.asyncExecution:
        thread = threading.Thread(target=orchestrator.execute_run, args=(run["id"],), daemon=True)
        thread.start()
        return run

    return orchestrator.execute_run(run["id"])


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> Dict[str, Any]:
    run = get_orchestrator().get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"FAROS run '{run_id}' not found")
    return run


@router.get("/runs/{run_id}/events")
async def get_run_events(run_id: str) -> Dict[str, Any]:
    run = get_orchestrator().get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"FAROS run '{run_id}' not found")
    events = get_orchestrator().list_events(run_id)
    return {"runId": run_id, "events": events, "total": len(events)}


@router.get("/runs/{run_id}/artifacts")
async def get_run_artifacts(run_id: str) -> Dict[str, Any]:
    run = get_orchestrator().get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"FAROS run '{run_id}' not found")
    artifacts = get_orchestrator().list_artifacts(run_id)
    return {"runId": run_id, "artifacts": artifacts, "total": len(artifacts)}
