"""Minimal code-module runtime facade.

This groups workspace and job-runner access behind the code module.
"""

from typing import Optional

from app.code.run.job_runner import JobRunner
from app.code.run.workspace import WorkspaceManager

_workspace_manager: Optional[WorkspaceManager] = None
_job_runner: Optional[JobRunner] = None


def get_workspace_manager() -> WorkspaceManager:
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager()
    return _workspace_manager


def get_job_runner() -> JobRunner:
    global _job_runner
    if _job_runner is None:
        _job_runner = JobRunner(get_workspace_manager())
    return _job_runner


__all__ = [
    "JobRunner",
    "WorkspaceManager",
    "get_job_runner",
    "get_workspace_manager",
]
