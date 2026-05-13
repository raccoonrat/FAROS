from typing import Iterable

from app.faros.models.artifact import ArtifactRecord
from app.faros.runtime.state_store import FarosStateStore


class ArtifactStore:
    """Persist artifact records emitted by capabilities."""

    def __init__(self, state_store: FarosStateStore):
        self.state_store = state_store

    def add(self, run_id: str, artifacts: Iterable[ArtifactRecord]) -> None:
        self.state_store.append_artifacts(run_id, [artifact.model_dump() for artifact in artifacts])
