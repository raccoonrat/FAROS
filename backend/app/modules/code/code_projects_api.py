"""
Code Projects API - GitHub-like browsing, search, export, VSCode link.

All responses use camelCase field names per frontend convention.
"""

import os
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.core.settings import get_settings
from app.modules.code.projects import code_project_service as cps, generate_project_from_plan, get_generation_status
from app.modules.code.storage import Session, crud, get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/code/projects", tags=["code_projects"])


# ============ Request / Response Schemas (camelCase) ============

class CreateProjectRequest(BaseModel):
    title: str
    description: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    license: Optional[str] = None
    sourceIdeaSessionId: Optional[str] = None
    sourceCandidateId: Optional[str] = None
    # If provided, write these files immediately
    files: Optional[List[dict]] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    license: Optional[str] = None
    sourceIdeaSessionId: Optional[str] = None
    sourceCandidateId: Optional[str] = None
    rootStoragePath: Optional[str] = None
    repoSchemaVersion: int = 1
    fileCount: int = 0
    totalSizeBytes: int = 0
    createdAt: str
    updatedAt: str


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int


class TreeEntry(BaseModel):
    name: str
    path: str
    isDir: bool
    size: int = 0


class TreeResponse(BaseModel):
    projectId: str
    path: str
    entries: List[TreeEntry]


class FileContentResponse(BaseModel):
    projectId: str
    path: str
    content: str
    size: int
    language: Optional[str] = None


class SearchResult(BaseModel):
    path: str
    line: Optional[int] = None
    content: Optional[str] = None
    isDir: bool = False


class SearchResponse(BaseModel):
    projectId: str
    query: str
    mode: str
    results: List[SearchResult]
    total: int


class ExportResponse(BaseModel):
    id: str
    projectId: str
    kind: str
    size: int
    sha256: Optional[str] = None
    createdAt: str


class VSCodeLinkResponse(BaseModel):
    uri: str
    path: str
    exists: bool
    instructions: str


# ============ Helpers ============

def _project_to_response(p) -> ProjectResponse:
    return ProjectResponse(
        id=p.id,
        title=p.title,
        description=p.description,
        language=p.language,
        framework=p.framework,
        license=p.license,
        sourceIdeaSessionId=p.source_idea_session_id,
        sourceCandidateId=p.source_candidate_id,
        rootStoragePath=p.root_storage_path,
        repoSchemaVersion=p.repo_schema_version,
        fileCount=p.file_count,
        totalSizeBytes=p.total_size_bytes,
        createdAt=p.created_at.isoformat() if p.created_at else "",
        updatedAt=p.updated_at.isoformat() if p.updated_at else "",
    )


def _guess_language(path: str) -> Optional[str]:
    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "typescriptreact", ".jsx": "javascriptreact",
        ".json": "json", ".md": "markdown", ".yml": "yaml", ".yaml": "yaml",
        ".html": "html", ".css": "css", ".sql": "sql", ".sh": "bash",
        ".toml": "toml", ".ini": "ini", ".cfg": "ini",
        ".rs": "rust", ".go": "go", ".java": "java",
        ".dockerfile": "dockerfile", ".xml": "xml",
    }
    _, ext = os.path.splitext(path.lower())
    if path.lower().endswith("dockerfile"):
        return "dockerfile"
    return ext_map.get(ext)


# ============ Endpoints ============

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Code Project",
)
async def create_project(
    request: CreateProjectRequest,
    db: Session = Depends(get_session),
) -> ProjectResponse:
    """Create a new code project. Optionally provide files to write immediately."""
    project = cps.create_project(
        db,
        title=request.title,
        description=request.description,
        language=request.language,
        framework=request.framework,
        license_str=request.license,
        source_idea_session_id=request.sourceIdeaSessionId,
        source_candidate_id=request.sourceCandidateId,
    )

    if request.files:
        cps.write_project_files(db, project.id, request.files)
        # Refresh project to get updated counts
        project = crud.get_project_v2(db, project.id)

    return _project_to_response(project)


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List Code Projects",
)
async def list_projects(
    search: Optional[str] = Query(None, description="Search by title"),
    language: Optional[str] = Query(None, description="Filter by language"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
) -> ProjectListResponse:
    projects = crud.list_projects_v2(db, search=search, language=language, limit=limit, offset=offset)
    return ProjectListResponse(
        projects=[_project_to_response(p) for p in projects],
        total=len(projects),
    )


@router.get(
    "/{projectId}",
    response_model=ProjectResponse,
    summary="Get Code Project",
)
async def get_project(
    projectId: str,
    db: Session = Depends(get_session),
) -> ProjectResponse:
    project = crud.get_project_v2(db, projectId)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {projectId}")
    return _project_to_response(project)


@router.delete(
    "/{projectId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Code Project",
)
async def delete_project(
    projectId: str,
    db: Session = Depends(get_session),
):
    project = crud.get_project_v2(db, projectId)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {projectId}")
    crud.delete_project_files(db, projectId)
    crud.delete_project_v2(db, projectId)


@router.get(
    "/{projectId}/tree",
    response_model=TreeResponse,
    summary="Get Project File Tree",
)
async def get_tree(
    projectId: str,
    path: str = Query("", description="Directory path to list"),
    db: Session = Depends(get_session),
) -> TreeResponse:
    project = crud.get_project_v2(db, projectId)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {projectId}")

    # Reject path traversal
    if ".." in path:
        raise HTTPException(status_code=400, detail="Path traversal not allowed")

    entries = cps.get_tree(db, projectId, path)
    return TreeResponse(
        projectId=projectId,
        path=path,
        entries=[TreeEntry(**e) for e in entries],
    )


@router.get(
    "/{projectId}/file",
    response_model=FileContentResponse,
    summary="Get File Content",
)
async def get_file(
    projectId: str,
    path: str = Query(..., description="File path within project"),
    db: Session = Depends(get_session),
) -> FileContentResponse:
    project = crud.get_project_v2(db, projectId)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {projectId}")

    if ".." in path:
        raise HTTPException(status_code=400, detail="Path traversal not allowed")

    content = cps.read_file_content(projectId, path)
    if content is None:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    return FileContentResponse(
        projectId=projectId,
        path=path,
        content=content,
        size=len(content.encode("utf-8")),
        language=_guess_language(path),
    )


@router.get(
    "/{projectId}/file/download",
    summary="Download Single File",
)
async def download_file(
    projectId: str,
    path: str = Query(..., description="File path within project"),
    db: Session = Depends(get_session),
):
    project = crud.get_project_v2(db, projectId)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {projectId}")

    if ".." in path:
        raise HTTPException(status_code=400, detail="Path traversal not allowed")

    abs_path = cps.get_file_abs_path(projectId, path)
    if not abs_path:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    filename = os.path.basename(path)
    return FileResponse(abs_path, filename=filename)


@router.get(
    "/{projectId}/search",
    response_model=SearchResponse,
    summary="Search Project Files",
)
async def search_project(
    projectId: str,
    q: str = Query(..., min_length=1, description="Search query"),
    mode: str = Query("path", description="Search mode: path or content"),
    db: Session = Depends(get_session),
) -> SearchResponse:
    project = crud.get_project_v2(db, projectId)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {projectId}")

    results = []

    if mode == "content":
        # Content search (grep-like)
        hits = cps.search_content(projectId, q)
        for h in hits:
            results.append(SearchResult(
                path=h["path"],
                line=h.get("line"),
                content=h.get("content"),
            ))
    else:
        # Path search via DB
        files = crud.search_project_files(db, projectId, q)
        for f in files:
            results.append(SearchResult(
                path=f.path,
                isDir=f.is_dir,
            ))

    return SearchResponse(
        projectId=projectId,
        query=q,
        mode=mode,
        results=results,
        total=len(results),
    )


@router.post(
    "/{projectId}/export",
    response_model=ExportResponse,
    summary="Export Project as ZIP",
)
async def export_project(
    projectId: str,
    db: Session = Depends(get_session),
) -> ExportResponse:
    project = crud.get_project_v2(db, projectId)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {projectId}")

    try:
        result = cps.export_zip(db, projectId)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ExportResponse(
        id=result["id"],
        projectId=result["projectId"],
        kind=result["kind"],
        size=result["size"],
        sha256=result.get("sha256"),
        createdAt=result["createdAt"],
    )


@router.get(
    "/{projectId}/vscode-link",
    response_model=VSCodeLinkResponse,
    summary="Get VSCode Open Link",
)
async def get_vscode_link(
    projectId: str,
    db: Session = Depends(get_session),
) -> VSCodeLinkResponse:
    project = crud.get_project_v2(db, projectId)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {projectId}")

    link = cps.get_vscode_link(projectId)
    return VSCodeLinkResponse(**link)


# ============ Export Download (separate route for export IDs) ============

@router.get(
    "/exports/{exportId}/download",
    summary="Download Export File",
)
async def download_export(
    exportId: str,
    db: Session = Depends(get_session),
):
    path = cps.get_export_path(db, exportId)
    if not path:
        raise HTTPException(status_code=404, detail=f"Export not found: {exportId}")

    filename = os.path.basename(path)
    return FileResponse(path, filename=filename, media_type="application/zip")


# ============ Generate Sample Project (convenience) ============

class GenerateSampleRequest(BaseModel):
    title: str
    language: str = "python"
    description: Optional[str] = None


@router.post(
    "/generate-sample",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Sample Project (for testing)",
)
async def generate_sample(
    request: GenerateSampleRequest,
    db: Session = Depends(get_session),
) -> ProjectResponse:
    project = cps.generate_sample_project(
        db,
        title=request.title,
        language=request.language,
        description=request.description,
    )
    # Refresh
    project = crud.get_project_v2(db, project.id)
    return _project_to_response(project)


# ============ Code Generation from Plan ============

class FromPlanRequest(BaseModel):
    planSessionId: str
    candidateId: str
    providerName: Optional[str] = None
    model: Optional[str] = None
    language: str = "python"
    framework: str = "FastAPI"
    enableWebSearch: bool = False
    enableGithub: bool = False


class FromPlanResponse(BaseModel):
    projectId: str
    status: str


def _run_code_agent(
    plan_session_id: str,
    candidate_id: str,
    provider_name: str,
    model: str,
    language: str,
    framework: str,
    enable_web_search: bool,
    enable_github: bool,
    existing_project_id: str = None,
):
    """Background task wrapper for code generation."""
    try:
        generate_project_from_plan(
            plan_session_id=plan_session_id,
            candidate_id=candidate_id,
            provider_name=provider_name,
            model=model,
            language=language,
            framework=framework,
            enable_web_search=enable_web_search,
            enable_github=enable_github,
            existing_project_id=existing_project_id,
        )
    except Exception as e:
        logger.error(f"Code agent background task failed: {e}", exc_info=True)


@router.post(
    "/from-plan",
    response_model=FromPlanResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate Project from Plan (async)",
)
async def create_from_plan(
    request: FromPlanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
):
    """Start code generation agent from a plan candidate. Returns immediately with projectId."""
    # Create a placeholder project in DB
    project = cps.create_project(
        db=db,
        title=f"Generating from plan...",
        language=request.language,
        description=f"Code generation in progress from plan session {request.planSessionId}",
    )
    project_id = project.id

    settings = get_settings()
    provider_name = request.providerName or settings.get_active_provider()
    model = request.model or settings.get_active_model(provider_name)

    # Launch background agent with existing project_id
    background_tasks.add_task(
        _run_code_agent,
        request.planSessionId,
        request.candidateId,
        provider_name,
        model,
        request.language,
        request.framework,
        request.enableWebSearch,
        request.enableGithub,
        project_id,
    )

    return FromPlanResponse(projectId=project_id, status="started")


@router.get(
    "/{projectId}/generation-status",
    summary="Get Code Generation Status",
)
async def get_project_generation_status(projectId: str):
    """Get step-by-step generation progress for a project."""
    status_data = get_generation_status(projectId)
    if not status_data:
        return {"projectId": projectId, "status": "unknown", "steps": [], "logs": []}
    return status_data
