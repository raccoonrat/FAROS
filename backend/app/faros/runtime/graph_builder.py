from typing import List

from app.faros.models.blueprint import Blueprint, WorkflowNode
from app.faros.models.execution import StepState


class GraphBuilder:
    """Build a linear execution plan from a blueprint."""

    def build(self, blueprint: Blueprint) -> List[WorkflowNode]:
        return blueprint.workflow

    def initial_step_states(self, blueprint: Blueprint) -> List[StepState]:
        return [
            StepState(node_id=node.id, capability=node.capability)
            for node in self.build(blueprint)
        ]
