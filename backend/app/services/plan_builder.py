"""
Plan Builder Service

Converts IdeaCandidate to ResearchPlan with proper schema compliance.
Handles the complex nested structure required by ResearchPlan model.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.models.idea import IdeaCandidate, DraftPlan
from app.models.research_plan import (
    ResearchPlan,
    Variables,
    Methodology,
    ExpectedOutcomes,
    ResearchApproach,
)

logger = logging.getLogger(__name__)


# Mapping from paper type to research approach
PAPER_TYPE_TO_APPROACH = {
    "algorithm": ResearchApproach.COMPARATIVE_TRAINING,
    "system": ResearchApproach.BASELINE_ESTABLISHMENT,
    "benchmark": ResearchApproach.BASELINE_ESTABLISHMENT,
    "survey": ResearchApproach.REPLICATION_STUDY,
    "application": ResearchApproach.COMPARATIVE_TRAINING,
    "theory": ResearchApproach.ABLATION_STUDY,
    "evaluation": ResearchApproach.COMPARATIVE_TRAINING,
    "reproducibility": ResearchApproach.REPLICATION_STUDY,
    "safety": ResearchApproach.ABLATION_STUDY,
    "position": ResearchApproach.COMPARATIVE_TRAINING,
}

# Default datasets by domain
DEFAULT_DATASETS = {
    "nlp": ["MMLU", "HumanEval", "GSM8K"],
    "cv": ["ImageNet", "COCO", "CIFAR-100"],
    "ml": ["UCI ML Repository", "Kaggle Benchmarks"],
    "rl": ["Atari", "MuJoCo", "OpenAI Gym"],
    "default": ["Standard Benchmark Dataset"],
}


def build_research_plan_from_candidate(
    candidate: IdeaCandidate,
    seed_query: str,
    paper_type: str,
    session_id: str,
    candidate_index: int,
    direction_id: Optional[str] = None,
) -> ResearchPlan:
    """
    Build a valid ResearchPlan from an IdeaCandidate.
    
    This function ensures all required fields are populated with valid values,
    using candidate data where available and generating defaults otherwise.
    
    Args:
        candidate: The selected idea candidate
        seed_query: Original research topic/query
        paper_type: Type of paper (algorithm, system, etc.)
        session_id: ID of the idea session
        direction_id: Optional research direction ID
    
    Returns:
        A valid ResearchPlan instance
    """
    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    
    # Build research question
    research_question = _build_research_question(candidate, seed_query)
    
    # Build hypothesis
    hypothesis = _build_hypothesis(candidate)
    
    # Build variables
    variables = _build_variables(candidate, seed_query)
    
    # Build methodology
    methodology = _build_methodology(candidate, paper_type, direction_id)
    
    # Build expected outcomes
    expected_outcomes = _build_expected_outcomes(candidate)
    
    # Build tags
    tags = _build_tags(candidate, paper_type, seed_query)
    
    # Build notes
    notes = _build_notes(candidate, session_id)
    
    return ResearchPlan(
        id=plan_id,
        research_question=research_question,
        hypothesis=hypothesis,
        variables=variables,
        methodology=methodology,
        expected_outcomes=expected_outcomes,
        tags=tags,
        notes=notes,
        source_session_id=session_id,
        source_candidate_id=candidate.id,
        source_candidate_index=candidate_index,
        source_title=candidate.title,
    )


def _build_research_question(candidate: IdeaCandidate, seed_query: str) -> str:
    """Build a proper research question from candidate data."""
    # Try to use draft plan's research question if available
    if candidate.draftPlan and candidate.draftPlan.researchQuestion:
        rq = candidate.draftPlan.researchQuestion
        if len(rq) >= 10:
            return rq
    
    # Build from problem statement
    problem = candidate.problem.strip()
    if problem and len(problem) >= 10:
        # Convert problem to question form if needed
        if not problem.endswith("?"):
            if problem.lower().startswith(("how", "what", "why", "can", "does", "is")):
                return problem + "?"
            else:
                return f"How can we address: {problem}?"
        return problem
    
    # Fallback: generate from title and seed
    return f"Can {candidate.title.lower()} improve performance in {seed_query}?"


def _build_hypothesis(candidate: IdeaCandidate) -> str:
    """Build a testable hypothesis from candidate data."""
    # Try draft plan hypothesis
    if candidate.draftPlan and candidate.draftPlan.hypothesis:
        hyp = candidate.draftPlan.hypothesis
        if len(hyp) >= 10:
            return hyp
    
    # Build from key insight
    insight = candidate.keyInsight.strip()
    if insight and len(insight) >= 10:
        if not insight.lower().startswith(("we hypothesize", "hypothesis:", "we expect")):
            return f"We hypothesize that {insight.lower()}"
        return insight
    
    # Fallback
    return f"Implementing {candidate.title} will lead to measurable improvements in the target metrics."


def _build_variables(candidate: IdeaCandidate, seed_query: str) -> Variables:
    """Build experimental variables from candidate data."""
    # Try to extract from draft plan
    if candidate.draftPlan and candidate.draftPlan.variables:
        vars_dict = candidate.draftPlan.variables
        if isinstance(vars_dict, dict):
            independent = vars_dict.get("independent", [])
            dependent = vars_dict.get("dependent", [])
            controls = vars_dict.get("controls", [])
            
            if independent and dependent:
                return Variables(
                    independent=independent if isinstance(independent, list) else [independent],
                    dependent=dependent if isinstance(dependent, list) else [dependent],
                    controls=controls if isinstance(controls, list) else [controls] if controls else [],
                )
    
    # Extract from experiments if available
    independent = []
    dependent = []
    controls = []
    
    if candidate.requiredExperiments:
        for exp in candidate.requiredExperiments:
            if exp.metrics:
                dependent.extend(exp.metrics)
    
    if candidate.expectedMetrics:
        dependent.extend(candidate.expectedMetrics)
    
    # Remove duplicates
    dependent = list(set(dependent)) if dependent else ["performance_metric", "accuracy"]
    
    # Generate independent variables from title/problem
    title_words = candidate.title.lower().split()
    if "method" in title_words or "approach" in title_words:
        independent.append("method_type")
    if "model" in title_words or "architecture" in title_words:
        independent.append("model_architecture")
    if "learning" in title_words:
        independent.append("learning_strategy")
    
    if not independent:
        independent = ["proposed_method"]
    
    # Default controls
    if not controls:
        controls = ["dataset_size", "random_seed", "hardware_configuration"]
    
    return Variables(
        independent=independent,
        dependent=dependent,
        controls=controls,
    )


def _build_methodology(
    candidate: IdeaCandidate,
    paper_type: str,
    direction_id: Optional[str],
) -> Methodology:
    """Build methodology specification from candidate data."""
    # Determine research approach
    approach = PAPER_TYPE_TO_APPROACH.get(paper_type, ResearchApproach.COMPARATIVE_TRAINING)
    
    # Determine direction ID
    if not direction_id:
        # Generate a reasonable direction ID from paper type and title
        title_slug = candidate.title.lower().replace(" ", "_")[:30]
        direction_id = f"{paper_type}_{title_slug}"
    
    # Determine datasets
    datasets = []
    if candidate.requiredExperiments:
        for exp in candidate.requiredExperiments:
            if exp.datasets:
                datasets.extend(exp.datasets)
    
    if not datasets:
        # Try to infer domain from seed query or title
        text = (candidate.title + " " + candidate.problem).lower()
        if any(w in text for w in ["language", "nlp", "text", "llm", "gpt"]):
            datasets = DEFAULT_DATASETS["nlp"]
        elif any(w in text for w in ["image", "vision", "visual", "cnn"]):
            datasets = DEFAULT_DATASETS["cv"]
        elif any(w in text for w in ["reinforcement", "agent", "policy"]):
            datasets = DEFAULT_DATASETS["rl"]
        else:
            datasets = DEFAULT_DATASETS["default"]
    
    # Remove duplicates
    datasets = list(set(datasets))
    
    return Methodology(
        direction_id=direction_id,
        approach=approach,
        datasets=datasets,
        template_id=None,
    )


def _build_expected_outcomes(candidate: IdeaCandidate) -> ExpectedOutcomes:
    """Build expected outcomes from candidate data."""
    # Try to get from draft plan
    if candidate.draftPlan and candidate.draftPlan.expectedOutcomes:
        outcomes = candidate.draftPlan.expectedOutcomes
        if outcomes and len(outcomes) > 0:
            primary_metric = outcomes[0] if isinstance(outcomes[0], str) else "performance"
            success_criteria = f"Achieve improvement in: {', '.join(outcomes[:3])}"
            return ExpectedOutcomes(
                primary_metric=primary_metric,
                baseline_value=None,
                target_value=None,
                success_criteria=success_criteria,
            )
    
    # Try to get from expected metrics
    if candidate.expectedMetrics:
        primary_metric = candidate.expectedMetrics[0]
        success_criteria = f"Demonstrate improvement in {primary_metric} compared to baseline methods"
        return ExpectedOutcomes(
            primary_metric=primary_metric,
            baseline_value=None,
            target_value=None,
            success_criteria=success_criteria,
        )
    
    # Try to get from experiments
    if candidate.requiredExperiments:
        for exp in candidate.requiredExperiments:
            if exp.metrics:
                primary_metric = exp.metrics[0]
                success_criteria = f"Achieve statistically significant improvement in {primary_metric}"
                return ExpectedOutcomes(
                    primary_metric=primary_metric,
                    baseline_value=None,
                    target_value=None,
                    success_criteria=success_criteria,
                )
    
    # Fallback
    return ExpectedOutcomes(
        primary_metric="performance_improvement",
        baseline_value=None,
        target_value=None,
        success_criteria="Demonstrate measurable improvement over existing baseline methods",
    )


def _build_tags(candidate: IdeaCandidate, paper_type: str, seed_query: str) -> List[str]:
    """Build tags from candidate data."""
    tags = []
    
    # Add paper type
    tags.append(paper_type)
    
    # Add from draft plan
    if candidate.draftPlan and candidate.draftPlan.tags:
        tags.extend(candidate.draftPlan.tags)
    
    # Extract keywords from seed query
    seed_words = seed_query.lower().split()
    important_words = [w for w in seed_words if len(w) > 4 and w not in 
                       ["about", "using", "based", "through", "between"]]
    tags.extend(important_words[:3])
    
    # Add "idea-generated" tag
    tags.append("idea-generated")
    
    # Remove duplicates and limit
    return list(set(tags))[:10]


def _build_notes(candidate: IdeaCandidate, session_id: str) -> str:
    """Build notes from candidate data."""
    notes_parts = [
        f"Generated from idea session: {session_id}",
        f"Candidate ID: {candidate.id}",
        f"Original title: {candidate.title}",
    ]
    
    if candidate.draftPlan and candidate.draftPlan.notes:
        notes_parts.append(f"Draft notes: {candidate.draftPlan.notes}")
    
    if candidate.risks:
        risk_summary = "; ".join([r.risk for r in candidate.risks[:3]])
        notes_parts.append(f"Key risks: {risk_summary}")
    
    # Add scores
    notes_parts.append(
        f"Scores - Novelty: {candidate.novelty:.1f}, "
        f"Feasibility: {candidate.feasibility:.1f}, "
        f"Impact: {candidate.impact:.1f}"
    )
    
    return "\n".join(notes_parts)


def candidate_to_plan_dict(
    candidate: IdeaCandidate,
    seed_query: str,
    paper_type: str,
    session_id: str,
    candidate_index: int,
    direction_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert candidate to a dictionary suitable for API response.
    
    This is useful when you need the plan data without creating a full
    ResearchPlan instance (e.g., for preview or validation).
    """
    plan = build_research_plan_from_candidate(
        candidate, seed_query, paper_type, session_id, candidate_index, direction_id
    )
    
    return {
        "id": plan.id,
        "research_question": plan.research_question,
        "hypothesis": plan.hypothesis,
        "variables": {
            "independent": plan.variables.independent,
            "dependent": plan.variables.dependent,
            "controls": plan.variables.controls,
        },
        "methodology": {
            "direction_id": plan.methodology.direction_id,
            "approach": plan.methodology.approach.value,
            "datasets": plan.methodology.datasets,
            "template_id": plan.methodology.template_id,
        },
        "expected_outcomes": {
            "primary_metric": plan.expected_outcomes.primary_metric,
            "baseline_value": plan.expected_outcomes.baseline_value,
            "target_value": plan.expected_outcomes.target_value,
            "success_criteria": plan.expected_outcomes.success_criteria,
        },
        "tags": plan.tags,
        "notes": plan.notes,
        "created_at": plan.created_at.isoformat(),
    }
