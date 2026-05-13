from typing import Any, Dict

from app.faros.capabilities.base import BaseCapability
from app.faros.models.artifact import ArtifactRecord
from app.faros.models.capability import CapabilityResult
from app.faros.models.execution import ExecutionContext
from app.modules.review.service import generate_review
from app.modules.review.storage import create_review


class ReviewerSimulationCapability(BaseCapability):
    capability_id = "reviewer_simulation"
    description = "Generate a structured paper review with actionable follow-up items."

    def execute(self, context: ExecutionContext, inputs: Dict[str, Any]) -> CapabilityResult:
        paper_id = inputs.get("paperId")
        if not paper_id:
            raise ValueError("reviewer_simulation requires paperId from a previous capability")

        binding = context.get_binding() or context.get_binding(self.capability_id)
        provider_name = binding.provider if binding else inputs.get("providerName", "moonshot")
        model = binding.model if binding and binding.model else inputs.get("model", "moonshot-v1-8k")

        record = create_review(
            {
                "paperId": paper_id,
                "reviewerProfile": inputs.get("reviewerProfile", "senior_reviewer"),
                "providerName": provider_name,
                "model": model,
            }
        )
        review = generate_review(record["id"])
        action_items = review.get("actionItems", [])

        return CapabilityResult(
            status="completed" if review.get("status") == "completed" else review.get("status", "failed"),
            outputs={
                "reviewId": review["id"],
                "reviewStatus": review.get("status"),
                "scoreSuggestion": review.get("scoreSuggestion"),
                "actionItemCount": len(action_items),
                "actionItems": action_items,
            },
            artifacts=[
                ArtifactRecord(
                    id=f"{context.run_id}:{self.capability_id}:review",
                    type="review_report",
                    uri=f"review://{review['id']}",
                    producer=self.capability_id,
                    summary=f"Review {review['id']} with {len(action_items)} action items",
                    metadata={"reviewId": review["id"], "paperId": paper_id},
                )
            ],
            events=[
                {
                    "level": "info",
                    "message": f"Reviewer simulation completed for paper {paper_id}",
                }
            ],
        )
