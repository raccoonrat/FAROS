"""
Code Session Model - Domain models for code generation sessions.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class CodeSessionStatus(str, Enum):
    """Session lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStep(str, Enum):
    """Pipeline step identifiers."""
    INTAKE = "intake"
    SEARCH = "search"
    SUMMARIZE = "summarize"
    GAP_ANALYSIS = "gap_analysis"
    CANDIDATE_GEN = "candidate_generation"
    RANKING = "ranking"
    SELECT = "select"
    APPLY = "apply"
    EVALUATE = "evaluate"
    REFINE = "refine"
    REPORT = "report"


@dataclass
class CodeSessionConfig:
    """Configuration for a code session."""
    repoPath: str
    goal: str
    providerName: str = "moonshot"
    model: str = "moonshot-v1-8k"
    maxCandidates: int = 3
    maxIterations: int = 3
    constraints: Optional[str] = None
    targetFiles: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "repoPath": self.repoPath,
            "goal": self.goal,
            "providerName": self.providerName,
            "model": self.model,
            "maxCandidates": self.maxCandidates,
            "maxIterations": self.maxIterations,
            "constraints": self.constraints,
            "targetFiles": self.targetFiles,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CodeSessionConfig":
        return CodeSessionConfig(
            repoPath=data["repoPath"],
            goal=data["goal"],
            providerName=data.get("providerName", "moonshot"),
            model=data.get("model", "moonshot-v1-8k"),
            maxCandidates=data.get("maxCandidates", 3),
            maxIterations=data.get("maxIterations", 3),
            constraints=data.get("constraints"),
            targetFiles=data.get("targetFiles"),
        )


@dataclass
class CandidateScores:
    """Scores for a code candidate."""
    correctness: float = 0.0
    completeness: float = 0.0
    efficiency: float = 0.0
    readability: float = 0.0
    safety: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "correctness": self.correctness,
            "completeness": self.completeness,
            "efficiency": self.efficiency,
            "readability": self.readability,
            "safety": self.safety,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CandidateScores":
        return CandidateScores(
            correctness=data.get("correctness", 0.0),
            completeness=data.get("completeness", 0.0),
            efficiency=data.get("efficiency", 0.0),
            readability=data.get("readability", 0.0),
            safety=data.get("safety", 0.0),
        )


@dataclass
class CodeCandidate:
    """A generated code candidate."""
    id: str
    sessionId: str
    title: str
    approach: str
    patch: str  # Unified diff format
    rationale: str
    scores: CandidateScores = field(default_factory=CandidateScores)
    overallScore: float = 0.0
    rank: int = 0
    evalReportId: Optional[str] = None
    createdAt: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sessionId": self.sessionId,
            "title": self.title,
            "approach": self.approach,
            "patch": self.patch,
            "rationale": self.rationale,
            "scores": self.scores.to_dict(),
            "overallScore": self.overallScore,
            "rank": self.rank,
            "evalReportId": self.evalReportId,
            "createdAt": self.createdAt,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CodeCandidate":
        return CodeCandidate(
            id=data["id"],
            sessionId=data["sessionId"],
            title=data["title"],
            approach=data["approach"],
            patch=data["patch"],
            rationale=data["rationale"],
            scores=CandidateScores.from_dict(data.get("scores", {})),
            overallScore=data.get("overallScore", 0.0),
            rank=data.get("rank", 0),
            evalReportId=data.get("evalReportId"),
            createdAt=data.get("createdAt", ""),
        )


@dataclass
class TraceStep:
    """A single step in the pipeline trace."""
    step: str
    status: str  # "started", "completed", "failed"
    timestamp: str
    durationMs: Optional[int] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "status": self.status,
            "timestamp": self.timestamp,
            "durationMs": self.durationMs,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TraceStep":
        return TraceStep(
            step=data["step"],
            status=data["status"],
            timestamp=data["timestamp"],
            durationMs=data.get("durationMs"),
            inputs=data.get("inputs"),
            outputs=data.get("outputs"),
            error=data.get("error"),
        )


@dataclass
class CodeSession:
    """A code generation session."""
    id: str
    status: CodeSessionStatus
    config: CodeSessionConfig
    createdAt: str
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    duration: Optional[int] = None
    currentStep: Optional[str] = None
    iterationCount: int = 0
    repoContextId: Optional[str] = None
    candidateIds: List[str] = field(default_factory=list)
    selectedCandidateId: Optional[str] = None
    evalReportId: Optional[str] = None
    trace: List[TraceStep] = field(default_factory=list)
    summary: Optional[str] = None
    errorMessage: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "config": self.config.to_dict(),
            "createdAt": self.createdAt,
            "startedAt": self.startedAt,
            "endedAt": self.endedAt,
            "duration": self.duration,
            "currentStep": self.currentStep,
            "iterationCount": self.iterationCount,
            "repoContextId": self.repoContextId,
            "candidateIds": self.candidateIds,
            "selectedCandidateId": self.selectedCandidateId,
            "evalReportId": self.evalReportId,
            "trace": [t.to_dict() for t in self.trace],
            "summary": self.summary,
            "errorMessage": self.errorMessage,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CodeSession":
        return CodeSession(
            id=data["id"],
            status=CodeSessionStatus(data["status"]),
            config=CodeSessionConfig.from_dict(data["config"]),
            createdAt=data["createdAt"],
            startedAt=data.get("startedAt"),
            endedAt=data.get("endedAt"),
            duration=data.get("duration"),
            currentStep=data.get("currentStep"),
            iterationCount=data.get("iterationCount", 0),
            repoContextId=data.get("repoContextId"),
            candidateIds=data.get("candidateIds", []),
            selectedCandidateId=data.get("selectedCandidateId"),
            evalReportId=data.get("evalReportId"),
            trace=[TraceStep.from_dict(t) for t in data.get("trace", [])],
            summary=data.get("summary"),
            errorMessage=data.get("errorMessage"),
        )
