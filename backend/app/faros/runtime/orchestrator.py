from datetime import datetime
from typing import Any, Dict, Optional

from app.faros.memory.research_memory import ResearchMemory
from app.faros.models.execution import ExecutionContext
from app.faros.registry.blueprint_registry import get_blueprint_registry
from app.faros.registry.capability_registry import get_capability_registry
from app.faros.registry.profile_registry import get_profile_registry
from app.faros.runtime.artifact_store import ArtifactStore
from app.faros.runtime.event_log import EventLog
from app.faros.runtime.graph_builder import GraphBuilder
from app.faros.runtime.state_store import FarosStateStore
from app.faros.verification.rules import DefaultCapabilityVerifier


class FarosOrchestrator:
    """Minimal FAROS orchestrator for the first release."""

    def __init__(self):
        self.blueprints = get_blueprint_registry()
        self.profiles = get_profile_registry()
        self.capabilities = get_capability_registry()
        self.state_store = FarosStateStore()
        self.graph_builder = GraphBuilder()
        self.event_log = EventLog(self.state_store)
        self.artifact_store = ArtifactStore(self.state_store)
        self.verifier = DefaultCapabilityVerifier()

    def create_run(self, blueprint_id: str, profile_id: str, inputs: Dict[str, Any], execution_mode: str = "execute") -> Dict[str, Any]:
        blueprint = self.blueprints.get(blueprint_id)
        self.profiles.get(profile_id)
        steps = self.graph_builder.initial_step_states(blueprint)
        return self.state_store.create_run(
            blueprint_id=blueprint_id,
            profile_id=profile_id,
            execution_mode=execution_mode,
            inputs=inputs,
            steps=steps,
        )

    def execute_run(self, run_id: str) -> Dict[str, Any]:
        run = self.state_store.get_run(run_id)
        if not run:
            raise ValueError(f"FAROS run '{run_id}' not found")

        blueprint = self.blueprints.get(run["blueprint_id"])
        profile = self.profiles.get(run["profile_id"])
        plan = self.graph_builder.build(blueprint)
        memory = ResearchMemory(self.state_store, run_id)

        self.state_store.update_run(
            run_id,
            {
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
            },
        )

        try:
            for node in plan:
                capability = self.capabilities.get(node.capability)
                self.state_store.update_step(
                    run_id,
                    node.id,
                    {
                        "status": "running",
                        "started_at": datetime.utcnow().isoformat(),
                    },
                )
                self.event_log.info(run_id, node.id, f"Executing capability {node.capability}")

                node_inputs = {}
                node_inputs.update(memory.data)
                node_inputs.update(node.inputs)

                context = ExecutionContext(
                    run_id=run_id,
                    blueprint_id=blueprint.id,
                    profile_id=profile.id,
                    node_id=node.id,
                    capability_id=node.capability,
                    provider_bindings=profile.capability_bindings,
                    memory=memory.data,
                    settings={"blueprintName": blueprint.name, "profileName": profile.name},
                )
                result = capability.execute(context, node_inputs)
                verification = self.verifier.verify(node.capability, result)
                if verification.status != "passed":
                    raise ValueError(verification.message)

                outputs_summary = {key: value for key, value in result.outputs.items() if key not in {"ideaCandidates", "actionItems"}}
                self.state_store.update_step(
                    run_id,
                    node.id,
                    {
                        "status": "completed",
                        "ended_at": datetime.utcnow().isoformat(),
                        "outputs_summary": outputs_summary,
                        "verification": verification.model_dump(),
                    },
                )
                self.artifact_store.add(run_id, result.artifacts)
                memory.merge(result.outputs)
                memory.update("lastNodeId", node.id)
                self.event_log.info(run_id, node.id, f"{node.capability} completed", verification=verification.model_dump())

            final_memory = self.state_store.get_memory(run_id)
            return self.state_store.update_run(
                run_id,
                {
                    "status": "completed",
                    "ended_at": datetime.utcnow().isoformat(),
                    "output_summary": {
                        "paperId": final_memory.get("paperId"),
                        "reviewId": final_memory.get("reviewId"),
                        "selectedCandidateId": final_memory.get("selectedCandidateId"),
                    },
                },
            )
        except Exception as exc:
            self.event_log.error(run_id, "runtime", "FAROS run failed", error=str(exc))
            return self.state_store.update_run(
                run_id,
                {
                    "status": "failed",
                    "ended_at": datetime.utcnow().isoformat(),
                    "error_message": str(exc),
                },
            )

    def list_runs(self) -> list[dict]:
        return self.state_store.list_runs()

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self.state_store.get_run(run_id)

    def list_events(self, run_id: str) -> list[dict]:
        return self.state_store.list_events(run_id)

    def list_artifacts(self, run_id: str) -> list[dict]:
        return self.state_store.list_artifacts(run_id)


_orchestrator: FarosOrchestrator | None = None


def get_orchestrator() -> FarosOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = FarosOrchestrator()
    return _orchestrator
