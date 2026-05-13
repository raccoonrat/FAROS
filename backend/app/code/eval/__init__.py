"""
Code Evaluation Module - Static and dynamic code evaluation.

Inspired by RepoExec's execution-based evaluation.
"""

from .static_eval import StaticEvaluator, StaticEvalResult
from .dynamic_eval import DynamicEvaluator, DynamicEvalResult
from .scoring import EvalScorer, EvalScore

__all__ = [
    "StaticEvaluator", "StaticEvalResult",
    "DynamicEvaluator", "DynamicEvalResult",
    "EvalScorer", "EvalScore",
]
