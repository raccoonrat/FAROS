from app.faros.models.capability import CapabilityResult
from app.faros.models.verification import VerificationResult
from app.faros.verification.base import BaseVerifier


class DefaultCapabilityVerifier(BaseVerifier):
    """Minimal verification rules for the first FAROS release."""

    REQUIRED_KEYS = {
        "idea_refinement": ["ideaSessionId", "candidateCount"],
        "experiment": ["projectId", "experimentId"],
        "paper_drafting": ["paperId", "paperStatus"],
        "reviewer_simulation": ["reviewId", "reviewStatus"],
    }

    def verify(self, capability_id: str, result: CapabilityResult) -> VerificationResult:
        required = self.REQUIRED_KEYS.get(capability_id, [])
        missing = [key for key in required if key not in result.outputs]
        if result.status != "completed":
            return VerificationResult(
                rule_id=f"{capability_id}:status",
                status="failed",
                message=f"{capability_id} did not complete successfully",
                details={"resultStatus": result.status},
            )
        if missing:
            return VerificationResult(
                rule_id=f"{capability_id}:schema",
                status="failed",
                message=f"{capability_id} result is missing required outputs",
                details={"missing": missing},
            )
        return VerificationResult(
            rule_id=f"{capability_id}:baseline",
            status="passed",
            message=f"{capability_id} passed baseline verification",
        )
