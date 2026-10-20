"""
Module 2: Automated Evaluation Engine.

Provides the Evaluation Triad:
  - Faithfulness (Groundedness / Hallucination Detection)
  - Answer Correctness (Semantic & Factual Alignment)
  - Context Precision (Retrieval Relevance)
"""
from AeroqAI.modules.module_2_evaluation.evaluator import (
    BaseEvaluator,
    DeterministicEvaluator,
    LLMJudgeEvaluator,
    get_evaluator
)

__all__ = [
    "BaseEvaluator",
    "DeterministicEvaluator",
    "LLMJudgeEvaluator",
    "get_evaluator"
]
