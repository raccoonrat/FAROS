"""Platform-owned skills API implementation."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillInfo(BaseModel):
    name: str
    description: str
    enabled: bool


class SkillsListResponse(BaseModel):
    skills: List[SkillInfo]
    total: int


class SkillExecRequest(BaseModel):
    skillName: str
    params: Dict[str, Any] = Field(default_factory=dict)


class SkillExecResponse(BaseModel):
    ok: bool
    skillName: str
    data: Any = None
    error: Optional[str] = None


def _get_registry():
    from app.agents.codegen.skills.registry import SkillsRegistry
    return SkillsRegistry()


@router.get("", response_model=SkillsListResponse, summary="List all agent skills")
async def list_skills() -> SkillsListResponse:
    registry = _get_registry()
    items = registry.list_skills()
    return SkillsListResponse(skills=[SkillInfo(**item) for item in items], total=len(items))


@router.post("/execute", response_model=SkillExecResponse, summary="Execute a skill")
async def execute_skill(req: SkillExecRequest) -> SkillExecResponse:
    registry = _get_registry()
    result = registry.execute(req.skillName, **req.params)
    return SkillExecResponse(ok=result.ok, skillName=req.skillName, data=result.data, error=result.error)
