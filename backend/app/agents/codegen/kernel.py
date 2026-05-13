"""
AgentKernel — OpenClaw-like orchestration for code generation.

Components:
- Planner: breaks task into steps based on plan context
- ToolRouter: chooses skills/tools for each step
- MemoryStore: persists intermediate artifacts
- Verifier: enforces constraints and quality gates
- PatchApplier: applies file diffs for repair cycles

The kernel runs a multi-phase pipeline:
1. Research & Context Gathering (web search, github, summarize)
2. Architecture Planning (file tree, module design)
3. Code Synthesis (batch + individual file generation)
4. Verification (compile check, structure validation, import sanity)
5. Repair Loop (detect issues → patch → re-verify, max 2 cycles)
6. Persist (write files, index, finalize)
"""

import json
import os
import re
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from app.llm.provider_client import get_provider_client, ChatMessage, ProviderClient
from app.agents.codegen.skills.registry import SkillsRegistry, SkillResult

logger = logging.getLogger(__name__)

# Storage for session traces
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_SESSIONS_DIR = os.path.join(_BASE_DIR, "data", "codegen_sessions")
os.makedirs(_SESSIONS_DIR, exist_ok=True)


@dataclass
class StepResult:
    name: str
    status: str  # "pending" | "running" | "ok" | "failed" | "skipped"
    detail: str = ""
    durationMs: int = 0
    toolCalls: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryStore:
    """Persists intermediate artifacts across agent steps."""
    references: List[Dict] = field(default_factory=list)
    github_repos: List[Dict] = field(default_factory=list)
    summaries: List[str] = field(default_factory=list)
    design_doc: Optional[str] = None
    file_tree: Optional[Dict] = None
    generated_files: Dict[str, str] = field(default_factory=dict)
    verification_results: List[Dict] = field(default_factory=list)
    patches_applied: int = 0

    def to_dict(self) -> Dict:
        return {
            "referenceCount": len(self.references),
            "githubRepoCount": len(self.github_repos),
            "summaryCount": len(self.summaries),
            "hasDesignDoc": self.design_doc is not None,
            "fileTreePlanned": self.file_tree is not None,
            "generatedFileCount": len(self.generated_files),
            "verificationCount": len(self.verification_results),
            "patchesApplied": self.patches_applied,
        }

    @staticmethod
    def from_dict(d: Dict) -> "MemoryStore":
        """Reconstruct MemoryStore from saved dict."""
        m = MemoryStore()
        m.references = [{} for _ in range(d.get("referenceCount", 0))]
        m.github_repos = [{} for _ in range(d.get("githubRepoCount", 0))]
        m.summaries = ["" for _ in range(d.get("summaryCount", 0))]
        m.design_doc = "(restored)" if d.get("hasDesignDoc") else None
        m.file_tree = {"files": []} if d.get("fileTreePlanned") else None
        m.generated_files = {f"file_{i}": "" for i in range(d.get("generatedFileCount", 0))}
        m.verification_results = [{} for _ in range(d.get("verificationCount", 0))]
        m.patches_applied = d.get("patchesApplied", 0)
        return m


@dataclass
class CodeGenSession:
    """Tracks a single code generation run."""
    id: str
    projectId: str
    planLinkId: Optional[str]
    providerName: str
    model: str
    status: str = "pending"  # pending | running | completed | failed
    steps: List[StepResult] = field(default_factory=list)
    memory: MemoryStore = field(default_factory=MemoryStore)
    config: Dict[str, Any] = field(default_factory=dict)
    createdAt: str = ""
    startedAt: Optional[str] = None
    completedAt: Optional[str] = None
    errorMessage: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "projectId": self.projectId,
            "planLinkId": self.planLinkId,
            "providerName": self.providerName,
            "model": self.model,
            "status": self.status,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status,
                    "detail": s.detail,
                    "durationMs": s.durationMs,
                    "toolCalls": s.toolCalls,
                }
                for s in self.steps
            ],
            "memory": self.memory.to_dict(),
            "config": self.config,
            "createdAt": self.createdAt,
            "startedAt": self.startedAt,
            "completedAt": self.completedAt,
            "errorMessage": self.errorMessage,
        }


# In-memory session store (also persisted to JSON files)
_sessions: Dict[str, CodeGenSession] = {}


def _gen_id() -> str:
    import uuid
    return f"cgs_{uuid.uuid4().hex[:12]}"


def _save_session(session: CodeGenSession):
    """Persist session to JSON file."""
    path = os.path.join(_SESSIONS_DIR, f"{session.id}.json")
    with open(path, "w") as f:
        json.dump(session.to_dict(), f, indent=2, default=str)


def get_session(session_id: str) -> Optional[CodeGenSession]:
    """Get session from memory or load from disk."""
    if session_id in _sessions:
        return _sessions[session_id]
    path = os.path.join(_SESSIONS_DIR, f"{session_id}.json")
    if os.path.isfile(path):
        with open(path) as f:
            data = json.load(f)
        session = CodeGenSession(
            id=data["id"],
            projectId=data["projectId"],
            planLinkId=data.get("planLinkId"),
            providerName=data["providerName"],
            model=data["model"],
            status=data["status"],
            createdAt=data["createdAt"],
            startedAt=data.get("startedAt"),
            completedAt=data.get("completedAt"),
            errorMessage=data.get("errorMessage"),
            config=data.get("config", {}),
        )
        # Reconstruct memory from saved counts
        mem_data = data.get("memory", {})
        if mem_data:
            session.memory = MemoryStore.from_dict(mem_data)
        for s in data.get("steps", []):
            session.steps.append(StepResult(
                name=s["name"], status=s["status"],
                detail=s.get("detail", ""), durationMs=s.get("durationMs", 0),
                toolCalls=s.get("toolCalls", []),
            ))
        _sessions[session_id] = session
        return session
    return None


def list_sessions(project_id: Optional[str] = None) -> List[Dict]:
    """List all sessions, optionally filtered by project."""
    # Load from disk
    results = []
    if os.path.isdir(_SESSIONS_DIR):
        for fname in sorted(os.listdir(_SESSIONS_DIR), reverse=True):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(_SESSIONS_DIR, fname)) as f:
                        data = json.load(f)
                    if project_id and data.get("projectId") != project_id:
                        continue
                    results.append(data)
                except Exception:
                    pass
    return results


def _extract_json(text: str) -> Optional[Dict]:
    """Extract JSON from LLM response text."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1]
        if "```" in text:
            text = text.rsplit("```", 1)[0]
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1]
        elif len(parts) >= 2:
            text = parts[1]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


# ── Prompt templates ──────────────────────────────────────────────────

DESIGN_DOC_PROMPT = """You are a senior software architect creating a PRODUCTION-GRADE design document.

**Plan Context:**
- Title: {title}
- Abstract: {abstract}
- Method: {method}
- Research Question: {research_question}
- Gap Analysis: {gap_analysis}

**References found:** {references}
**Similar repos:** {repos}

Write a comprehensive design document (800-1200 words) covering ALL of the following:

1. **System Architecture Overview** — layered architecture: API layer, service/domain layer, storage/repository layer, database layer, utility layer.
2. **Module Inventory** — at least 8 modules/packages with clear responsibilities.
3. **Database Design** — SQLite schema with at least 4 tables including migrations plan. Describe each table, columns, relationships.
4. **API Design** — RESTful endpoints grouped by resource. Describe request/response schemas.
5. **Configuration Management** — environment variables, config classes, secrets handling.
6. **Logging & Observability** — structured logging, log levels, key instrumentation points.
7. **Caching Strategy** — what to cache, TTL policy, invalidation.
8. **Data Flow** — request lifecycle from API → service → storage → DB → response.
9. **Testing Strategy** — unit tests (per module), integration tests (API-level), fixtures, mocking strategy.
10. **CI/CD Pipeline** — linting (ruff/black), type checking (mypy), test execution, coverage reporting.
11. **Evaluation Harness** — scaffolding for benchmarking: metrics collection, dataset loading, result persistence.
12. **Security** — input validation, path sanitization, no raw secret logging.

Return plain text Markdown (no JSON).
"""

FILE_TREE_PROMPT = """You are a senior software architect. Design a PRODUCTION-GRADE project file tree.

**Design Document:**
{design_doc}

**Language:** {language}
**Framework:** {framework}

**MANDATORY structure (ALL must be present):**

1. **Root configs (≥6 files):** README.md, requirements.txt (or package.json), pyproject.toml (or tsconfig.json), .gitignore, Makefile, Dockerfile, .env.example
2. **CI/CD (≥2 files):** .github/workflows/ci.yml, .github/workflows/lint.yml
3. **Source — API layer (≥4 files):** src/api/ or app/api/ with routers, schemas, middleware, deps
4. **Source — Service/Domain (≥5 files):** src/services/ or app/services/ with business logic modules
5. **Source — Storage/Repository (≥3 files):** src/storage/ or app/storage/ with repository pattern, queries
6. **Source — Database (≥4 files):** src/db/ with engine.py, models.py, migrations/, seed.py (SQLite)
7. **Source — Core/Config (≥3 files):** config.py, logging_config.py, constants.py, cache.py
8. **Source — Utils (≥2 files):** src/utils/ with helpers, validators
9. **Tests — Unit (≥5 files):** tests/unit/ with test files per module
10. **Tests — Integration (≥3 files):** tests/integration/ with API-level tests, fixtures
11. **Tests — conftest (1 file):** tests/conftest.py with shared fixtures
12. **Docs (≥3 files):** docs/architecture.md, docs/api.md, docs/getting-started.md
13. **Scripts (≥2 files):** scripts/seed_db.py, scripts/run_eval.py
14. **Evaluation harness (≥2 files):** evaluation/harness.py, evaluation/metrics.py
15. **Data (≥1 file):** data/.gitkeep or data/sample.json

**Total: MUST have at least 45 files.**

**Output (strict JSON):**
```json
{{
  "projectName": "name",
  "description": "brief",
  "files": [
    {{"path": "relative/path", "description": "purpose", "type": "source|test|config|doc|ci|data|script|eval"}}
  ]
}}
```

Return ONLY valid JSON. Count your files — MUST be >= 45.
"""

BATCH_CODE_PROMPT = """You are an expert {language} developer building a PRODUCTION-GRADE research project.

**Project:** {project_name}
**Description:** {description}
**Design:** {design_summary}

Generate content for ALL files below. Return strict JSON.

**Files:**
{files_list}

**Output (strict JSON):**
```json
{{
  "files": [
    {{"path": "exact/path", "content": "full file content"}}
  ]
}}
```

**MANDATORY quality requirements:**
- Every Python file: proper imports, docstrings, type hints, logging
- Database models: SQLAlchemy ORM with SQLite, at least 4 tables with relationships
- Migration: alembic-style init script or explicit CREATE TABLE SQL
- Config: pydantic Settings class reading from .env
- API routes: FastAPI routers with Pydantic schemas, proper HTTP status codes, error handling
- Services: business logic separated from API, dependency injection pattern
- Storage: repository pattern with CRUD operations
- Cache: simple in-memory or file-based cache utility with TTL
- Logging: structured logging with module-level loggers, log config file
- Tests: real assertions (not just pass), fixtures in conftest.py, at least 3 test functions per test file
- CI: GitHub Actions workflow running lint + test
- README: 200+ words with Installation, Quick Start, Architecture, Testing, API sections
- Makefile: targets for install, lint, test, run, docker-build
- Dockerfile: multi-stage build
- Evaluation harness: load data → run model → compute metrics → save results
- .env.example: all environment variables with descriptions
- No placeholder TODOs — every file must have real, functional content

Return ONLY valid JSON.
"""

SINGLE_FILE_PROMPT = """Generate the COMPLETE content for this file in a {language} research project.

**Project:** {project_name} — {description}
**File:** {file_path} ({file_type}) — {file_description}
**Context files:** {context}

Write production-quality code. Return ONLY the file content, no markdown fences.
"""

REPAIR_PROMPT = """You are a code repair assistant. Fix the issues below in the project files.

**Issues found:**
{issues}

**Current file contents:**
{file_contents}

For each issue, provide a fix. Return strict JSON:
```json
{{
  "patches": [
    {{"path": "file/path", "content": "complete corrected file content"}}
  ]
}}
```

Return ONLY valid JSON.
"""


# ── AgentKernel ──────────────────────────────────────────────────────

class AgentKernel:
    """OpenClaw-like agent orchestrator for code generation."""

    def __init__(
        self,
        provider_name: str = "moonshot",
        model: str = "moonshot-v1-8k",
        language: str = "python",
        framework: str = "FastAPI",
        enable_web_search: bool = True,
        enable_github: bool = True,
        max_repair_cycles: int = 2,
    ):
        self.provider_name = provider_name
        self.model = model
        self.language = language
        self.framework = framework
        self.enable_web_search = enable_web_search
        self.enable_github = enable_github
        self.max_repair_cycles = max_repair_cycles

        self.client: ProviderClient = get_provider_client(provider_name)
        self.skills = SkillsRegistry(self.client, model)
        if not enable_web_search:
            self.skills.disable("webSearch")
        if not enable_github:
            self.skills.disable("githubSearch")
            self.skills.disable("githubFetchRepo")

    def _run_step(self, session: CodeGenSession, name: str, fn, *args, **kwargs) -> Any:
        """Execute a step with timing and status tracking."""
        step = StepResult(name=name, status="running")
        session.steps.append(step)
        _save_session(session)

        t0 = time.time()
        try:
            result = fn(session, *args, **kwargs)
            step.status = "ok"
            step.durationMs = int((time.time() - t0) * 1000)
            _save_session(session)
            return result
        except Exception as e:
            step.status = "failed"
            step.detail = str(e)[:500]
            step.durationMs = int((time.time() - t0) * 1000)
            _save_session(session)
            raise

    def run(
        self,
        session: CodeGenSession,
        title: str,
        abstract: str,
        method: str,
        research_question: str,
        gap_analysis: str = "",
    ) -> str:
        """
        Execute the full code generation pipeline.
        Returns project_id.
        """
        session.status = "running"
        session.startedAt = datetime.utcnow().isoformat()
        _save_session(session)

        try:
            # Phase 1: Research & Context
            self._run_step(session, "research_web_search", self._step_web_search, title, abstract)
            self._run_step(session, "research_github_search", self._step_github_search, title)
            self._run_step(session, "research_summarize", self._step_summarize, session, title, abstract)

            # Phase 2: Architecture
            self._run_step(session, "design_document", self._step_design_doc, session, title, abstract, method, research_question, gap_analysis)
            self._run_step(session, "plan_file_tree", self._step_plan_tree, session)

            # Phase 3: Code Synthesis
            self._run_step(session, "code_synthesis_batch", self._step_synthesize_batch, session, title)
            self._run_step(session, "code_synthesis_fill", self._step_synthesize_fill, session, title)

            # Phase 4: Verification
            self._run_step(session, "verify_structure", self._step_verify, session)

            # Phase 5: Repair Loop (max 2 cycles)
            for cycle in range(self.max_repair_cycles):
                issues = session.memory.verification_results
                error_issues = [i for i in issues if i.get("severity") == "error"] if issues else []
                if not error_issues:
                    break
                self._run_step(session, f"repair_cycle_{cycle + 1}", self._step_repair, session, error_issues)
                self._run_step(session, f"re_verify_{cycle + 1}", self._step_verify, session)

            # Phase 6: Persist
            self._run_step(session, "persist_files", self._step_persist, session)

            session.status = "completed"
            session.completedAt = datetime.utcnow().isoformat()
            _save_session(session)
            return session.projectId

        except Exception as e:
            logger.error(f"Agent kernel failed: {e}", exc_info=True)
            session.status = "failed"
            session.errorMessage = str(e)[:1000]
            session.completedAt = datetime.utcnow().isoformat()
            _save_session(session)
            raise

    # ── Step implementations ──────────────────────────────────────

    def _step_web_search(self, session: CodeGenSession, title: str, abstract: str):
        result = self.skills.execute("webSearch", query=f"{title} {abstract[:100]}")
        step = session.steps[-1]
        step.toolCalls.append({"skill": "webSearch", "ok": result.ok})
        if result.ok and result.data:
            session.memory.references = result.data if isinstance(result.data, list) else []
            step.detail = f"Found {len(session.memory.references)} references"
        else:
            step.status = "skipped"
            step.detail = result.error or "No results"

    def _step_github_search(self, session: CodeGenSession, title: str):
        result = self.skills.execute("githubSearch", query=title)
        step = session.steps[-1]
        step.toolCalls.append({"skill": "githubSearch", "ok": result.ok})
        if result.ok and result.data:
            session.memory.github_repos = result.data if isinstance(result.data, list) else []
            step.detail = f"Found {len(session.memory.github_repos)} repos"
        else:
            step.status = "skipped"
            step.detail = result.error or "No results"

    def _step_summarize(self, session: CodeGenSession, _session_arg: CodeGenSession, title: str, abstract: str):
        text_to_summarize = f"Title: {title}\nAbstract: {abstract}\nReferences: {json.dumps(session.memory.references[:3], default=str)}"
        result = self.skills.execute("summarize", text=text_to_summarize)
        step = session.steps[-1]
        step.toolCalls.append({"skill": "summarize", "ok": result.ok})
        if result.ok:
            session.memory.summaries.append(result.data)
            step.detail = "Summarized plan context"
        else:
            step.status = "skipped"
            step.detail = result.error or "Failed"

    def _step_design_doc(self, session: CodeGenSession, _session_arg, title, abstract, method, rq, gap):
        refs_str = json.dumps(session.memory.references[:5], default=str)[:500]
        repos_str = json.dumps(session.memory.github_repos[:3], default=str)[:500]
        prompt = DESIGN_DOC_PROMPT.format(
            title=title, abstract=abstract, method=method,
            research_question=rq, gap_analysis=gap,
            references=refs_str, repos=repos_str,
        )
        resp = self.client.chat(messages=[ChatMessage(role="user", content=prompt)], model=self.model, temperature=0.4, max_tokens=2000)
        session.memory.design_doc = resp.text.strip()
        step = session.steps[-1]
        step.detail = f"Design doc: {len(session.memory.design_doc)} chars"

    def _step_plan_tree(self, session: CodeGenSession, _session_arg):
        result = self.skills.execute(
            "planFileTree",
            plan_context=session.memory.design_doc or "Research project",
            language=self.language,
            framework=self.framework,
        )
        step = session.steps[-1]
        step.toolCalls.append({"skill": "planFileTree", "ok": result.ok})
        if result.ok and result.data:
            session.memory.file_tree = result.data
            file_count = len(result.data.get("files", []))
            step.detail = f"Planned {file_count} files"
        else:
            # Fallback to default tree
            session.memory.file_tree = self._default_file_tree()
            step.detail = f"Used fallback tree ({len(session.memory.file_tree['files'])} files)"

    def _step_synthesize_batch(self, session: CodeGenSession, _session_arg, title: str):
        tree = session.memory.file_tree
        if not tree:
            raise ValueError("No file tree planned")

        files = tree.get("files", [])
        project_name = tree.get("projectName", title)
        description = tree.get("description", "")
        design_summary = (session.memory.design_doc or "")[:1500]

        files_list_str = "\n".join([
            f"- {f['path']}: {f.get('description', '')} ({f.get('type', 'source')})"
            for f in files
        ])

        prompt = BATCH_CODE_PROMPT.format(
            language=self.language,
            project_name=project_name,
            description=description,
            design_summary=design_summary,
            files_list=files_list_str,
        )

        resp = self.client.chat(messages=[ChatMessage(role="user", content=prompt)], model=self.model, temperature=0.4, max_tokens=8000)
        parsed = _extract_json(resp.text)

        if parsed and "files" in parsed:
            for f in parsed["files"]:
                path = f.get("path", "")
                content = f.get("content", "")
                if path and content:
                    session.memory.generated_files[path] = content

        step = session.steps[-1]
        step.detail = f"Batch synthesized {len(session.memory.generated_files)} files"

    def _step_synthesize_fill(self, session: CodeGenSession, _session_arg, title: str):
        tree = session.memory.file_tree
        if not tree:
            return

        files = tree.get("files", [])
        project_name = tree.get("projectName", title)
        description = tree.get("description", "")
        missing = [f for f in files if f["path"] not in session.memory.generated_files]

        filled = 0
        for f in missing:
            try:
                context = ", ".join(list(session.memory.generated_files.keys())[:10])
                prompt = SINGLE_FILE_PROMPT.format(
                    language=self.language,
                    project_name=project_name,
                    description=description,
                    file_path=f["path"],
                    file_type=f.get("type", "source"),
                    file_description=f.get("description", ""),
                    context=context,
                )
                resp = self.client.chat(messages=[ChatMessage(role="user", content=prompt)], model=self.model, temperature=0.3, max_tokens=2000)
                content = resp.text.strip()
                if content.startswith("```"):
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
                session.memory.generated_files[f["path"]] = content
                filled += 1
            except Exception as e:
                logger.warning(f"Failed to fill {f['path']}: {e}")
                session.memory.generated_files[f["path"]] = f"# {f['path']}\n# Generation failed: {e}\n"

        step = session.steps[-1]
        step.detail = f"Filled {filled} missing files (total: {len(session.memory.generated_files)})"

    def _step_verify(self, session: CodeGenSession, _session_arg):
        result = self.skills.execute(
            "compileCheck",
            project_root="",
            language=self.language,
            files=session.memory.generated_files,
        )
        step = session.steps[-1]
        step.toolCalls.append({"skill": "compileCheck", "ok": result.ok})
        if result.ok:
            issues = result.data.get("issues", []) if result.data else []
            session.memory.verification_results = issues
            step.detail = f"Verified: {result.data.get('fileCount', 0)} files, {result.data.get('errorCount', 0)} errors"
        else:
            session.memory.verification_results = []
            step.detail = result.error or "Verification failed"

    def _step_repair(self, session: CodeGenSession, _session_arg, error_issues: List[Dict]):
        issues_str = json.dumps(error_issues[:10], indent=2)
        # Show relevant file contents
        affected_files = set(i.get("file", "") for i in error_issues if i.get("file") != "*")
        file_contents_str = ""
        for path in list(affected_files)[:5]:
            content = session.memory.generated_files.get(path, "")
            file_contents_str += f"\n--- {path} ---\n{content[:1000]}\n"

        prompt = REPAIR_PROMPT.format(issues=issues_str, file_contents=file_contents_str)
        resp = self.client.chat(messages=[ChatMessage(role="user", content=prompt)], model=self.model, temperature=0.2, max_tokens=4000)
        parsed = _extract_json(resp.text)

        patches_applied = 0
        if parsed and "patches" in parsed:
            for patch in parsed["patches"]:
                path = patch.get("path", "")
                content = patch.get("content", "")
                if path and content and path in session.memory.generated_files:
                    session.memory.generated_files[path] = content
                    patches_applied += 1

        session.memory.patches_applied += patches_applied
        step = session.steps[-1]
        step.detail = f"Applied {patches_applied} patches"

    def _step_persist(self, session: CodeGenSession, _session_arg):
        files = session.memory.generated_files
        if not files:
            raise ValueError("No files to persist")

        files_list = [{"path": p, "content": c} for p, c in files.items()]
        result = self.skills.execute("writeProjectFiles", project_id=session.projectId, files=files_list)

        step = session.steps[-1]
        step.toolCalls.append({"skill": "writeProjectFiles", "ok": result.ok})
        if result.ok:
            step.detail = f"Wrote {result.data['fileCount']} files ({result.data['totalBytes']} bytes)"
        else:
            raise ValueError(f"Failed to persist: {result.error}")

    def _default_file_tree(self) -> Dict:
        """Fallback file tree if LLM planning fails. Produces 48 files for project-grade output."""
        ext = "py" if self.language.lower() == "python" else "ts"
        py = ext == "py"
        return {
            "projectName": "research-project",
            "description": "Production-grade research project with DB, tests, CI, and evaluation harness",
            "files": [
                # Root configs (7)
                {"path": "README.md", "description": "Project readme with setup, architecture, API docs", "type": "doc"},
                {"path": "requirements.txt" if py else "package.json", "description": "Dependencies", "type": "config"},
                {"path": "pyproject.toml" if py else "tsconfig.json", "description": "Project config", "type": "config"},
                {"path": ".gitignore", "description": "Git ignore rules", "type": "config"},
                {"path": "Makefile", "description": "Build/lint/test/run targets", "type": "config"},
                {"path": "Dockerfile", "description": "Multi-stage container build", "type": "config"},
                {"path": ".env.example", "description": "Environment variable template", "type": "config"},
                # CI (2)
                {"path": ".github/workflows/ci.yml", "description": "CI pipeline: lint + test", "type": "ci"},
                {"path": ".github/workflows/lint.yml", "description": "Linting workflow", "type": "ci"},
                # API layer (5)
                {"path": f"src/__init__.{ext}" if py else "src/index.ts", "description": "Package init", "type": "source"},
                {"path": f"src/api/__init__.{ext}" if py else "src/api/index.ts", "description": "API package init", "type": "source"},
                {"path": f"src/api/router.{ext}", "description": "Main API router with all routes", "type": "source"},
                {"path": f"src/api/schemas.{ext}", "description": "Pydantic request/response schemas", "type": "source"},
                {"path": f"src/api/middleware.{ext}", "description": "Request logging, error handling middleware", "type": "source"},
                # Services (5)
                {"path": f"src/services/__init__.{ext}" if py else "src/services/index.ts", "description": "Services init", "type": "source"},
                {"path": f"src/services/pipeline_service.{ext}", "description": "Core processing pipeline", "type": "source"},
                {"path": f"src/services/analysis_service.{ext}", "description": "Analysis and computation logic", "type": "source"},
                {"path": f"src/services/export_service.{ext}", "description": "Export and formatting service", "type": "source"},
                {"path": f"src/services/cache_service.{ext}", "description": "In-memory cache with TTL", "type": "source"},
                # Storage (3)
                {"path": f"src/storage/__init__.{ext}" if py else "src/storage/index.ts", "description": "Storage init", "type": "source"},
                {"path": f"src/storage/repository.{ext}", "description": "Repository pattern CRUD", "type": "source"},
                {"path": f"src/storage/queries.{ext}", "description": "SQL query builders", "type": "source"},
                # Database (4)
                {"path": f"src/db/__init__.{ext}" if py else "src/db/index.ts", "description": "DB init", "type": "source"},
                {"path": f"src/db/engine.{ext}", "description": "SQLite engine setup", "type": "source"},
                {"path": f"src/db/models.{ext}", "description": "ORM models (4+ tables)", "type": "source"},
                {"path": f"src/db/migrations.{ext}", "description": "Migration scripts", "type": "source"},
                {"path": f"src/db/seed.{ext}", "description": "Seed data loader", "type": "source"},
                # Core/Config (4)
                {"path": f"src/main.{ext}", "description": "Application entry point", "type": "source"},
                {"path": f"src/config.{ext}", "description": "Settings class reading .env", "type": "source"},
                {"path": f"src/logging_config.{ext}", "description": "Structured logging setup", "type": "source"},
                {"path": f"src/constants.{ext}", "description": "Project constants", "type": "source"},
                # Utils (2)
                {"path": f"src/utils/__init__.{ext}" if py else "src/utils/index.ts", "description": "Utils init", "type": "source"},
                {"path": f"src/utils/validators.{ext}", "description": "Input validators", "type": "source"},
                # Tests unit (6)
                {"path": f"tests/__init__.{ext}" if py else "tests/setup.ts", "description": "Tests init", "type": "test"},
                {"path": "tests/conftest.py" if py else "tests/helpers.ts", "description": "Shared fixtures", "type": "test"},
                {"path": f"tests/unit/__init__.{ext}" if py else "tests/unit/setup.ts", "description": "Unit tests init", "type": "test"},
                {"path": f"tests/unit/test_pipeline.{ext}", "description": "Pipeline service tests", "type": "test"},
                {"path": f"tests/unit/test_analysis.{ext}", "description": "Analysis service tests", "type": "test"},
                {"path": f"tests/unit/test_models.{ext}", "description": "DB model tests", "type": "test"},
                {"path": f"tests/unit/test_repository.{ext}", "description": "Repository tests", "type": "test"},
                {"path": f"tests/unit/test_cache.{ext}", "description": "Cache tests", "type": "test"},
                # Tests integration (3)
                {"path": f"tests/integration/__init__.{ext}" if py else "tests/integration/setup.ts", "description": "Integration init", "type": "test"},
                {"path": f"tests/integration/test_api.{ext}", "description": "API endpoint tests", "type": "test"},
                {"path": f"tests/integration/test_db.{ext}", "description": "DB integration tests", "type": "test"},
                # Docs (3)
                {"path": "docs/architecture.md", "description": "Architecture overview", "type": "doc"},
                {"path": "docs/api.md", "description": "API endpoint documentation", "type": "doc"},
                {"path": "docs/getting-started.md", "description": "Quickstart guide", "type": "doc"},
                # Scripts (2)
                {"path": f"scripts/seed_db.{ext}", "description": "Database seeding script", "type": "script"},
                {"path": f"scripts/run_eval.{ext}", "description": "Run evaluation harness", "type": "script"},
                # Evaluation (2)
                {"path": f"evaluation/__init__.{ext}" if py else "evaluation/index.ts", "description": "Eval init", "type": "eval"},
                {"path": f"evaluation/harness.{ext}", "description": "Evaluation harness runner", "type": "eval"},
                {"path": f"evaluation/metrics.{ext}", "description": "Evaluation metrics computation", "type": "eval"},
                # Data (1)
                {"path": "data/.gitkeep", "description": "Data directory placeholder", "type": "data"},
            ],
        }
