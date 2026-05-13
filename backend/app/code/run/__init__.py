"""
Code Run Module - Workspace management and job execution.

Provides:
- Workspace creation and management
- Patch application
- Job execution with logging
- Process management
"""

from .workspace import WorkspaceManager
from .job_runner import JobRunner

__all__ = ["WorkspaceManager", "JobRunner"]
