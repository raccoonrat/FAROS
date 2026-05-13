"""
Database Module - SQLite with SQLModel for Phase 2.1

Provides:
- SQLModel-based ORM models
- Alembic migrations
- Session management
- Connection pooling (for future Postgres migration)
"""

from .engine import get_engine, get_session, init_db, get_migration_status, test_connection
from .models import (
    CodeProject, CodeProjectCreate,
    CodeSessionDB, CodeSessionCreate,
    RepoContextDB, RepoContextCreate,
    CodeCandidateDB, CodeCandidateCreate,
    CodeJob, CodeJobCreate, JobStatus,
    EvalReportDB, EvalReportCreate,
    TraceLogDB, TraceLogCreate,
    ArtifactDB, ArtifactCreate, ArtifactKind,
)

__all__ = [
    "get_engine", "get_session", "init_db", "get_migration_status", "test_connection",
    "CodeProject", "CodeProjectCreate",
    "CodeSessionDB", "CodeSessionCreate", 
    "RepoContextDB", "RepoContextCreate",
    "CodeCandidateDB", "CodeCandidateCreate",
    "CodeJob", "CodeJobCreate", "JobStatus",
    "EvalReportDB", "EvalReportCreate",
    "TraceLogDB", "TraceLogCreate",
    "ArtifactDB", "ArtifactCreate", "ArtifactKind",
]
