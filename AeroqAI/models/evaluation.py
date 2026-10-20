"""Data contracts and schemas for Module 2: Automated Evaluation Engine."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EvaluationSample(BaseModel):
    """
    A single ground-truth benchmark test case for RAG evaluation.
    """
    sample_id: str = Field(..., description="Unique sample identifier (e.g., sample_leave_01)")
    query: str = Field(..., description="The user query or benchmark prompt")
    ground_truth_answer: str = Field(..., description="The authoritative reference answer")
    reference_contexts: List[str] = Field(default_factory=list, description="Ground truth reference passages from the source documents")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as source page, category, difficulty")


class MetricScore(BaseModel):
    """A scored metric with numerical rating and explanatory reasoning."""
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized score between 0.0 (fail) and 1.0 (perfect)")
    reasoning: str = Field("", description="Explanatory justification for the assigned score")


class SampleEvaluationResult(BaseModel):
    """
    Complete evaluation assessment for a single query sample across the Evaluation Triad.
    """
    sample_id: str = Field(..., description="Identifier matching the evaluated sample")
    query: str = Field(..., description="The evaluated user query")
    generated_answer: str = Field(..., description="Answer produced by the RAG pipeline")
    ground_truth_answer: str = Field(..., description="Expected reference answer")
    retrieved_contexts: List[str] = Field(default_factory=list, description="Retrieved passages used to generate the answer")
    
    # Triad Metrics
    faithfulness: MetricScore = Field(..., description="Hallucination check: is answer grounded in context?")
    answer_correctness: MetricScore = Field(..., description="Semantic alignment: does answer match ground truth?")
    context_precision: MetricScore = Field(..., description="Retrieval quality: are retrieved chunks relevant?")
    
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Weighted composite score across triad metrics")
    passed: bool = Field(..., description="Whether overall score satisfies the threshold")
    eval_latency_ms: float = Field(0.0, description="Evaluation execution latency in milliseconds")


class BenchmarkReport(BaseModel):
    """
    Aggregated benchmark report over an entire evaluation dataset.
    """
    dataset_name: str = Field(..., description="Name of the benchmark evaluation dataset")
    evaluator_model: str = Field(..., description="Model or engine used to compute evaluations")
    total_samples: int = Field(..., description="Number of evaluated query cases")
    passed_samples: int = Field(..., description="Count of samples satisfying the pass threshold")
    failed_samples: int = Field(..., description="Count of samples failing the pass threshold")
    pass_rate: float = Field(..., description="Percentage of passing samples (0.0 to 100.0)")
    
    # Aggregate Triad Averages
    mean_faithfulness: float = Field(..., description="Average faithfulness score (0.0 to 1.0)")
    mean_correctness: float = Field(..., description="Average answer correctness score (0.0 to 1.0)")
    mean_context_precision: float = Field(..., description="Average context precision score (0.0 to 1.0)")
    mean_overall_score: float = Field(..., description="Average composite score (0.0 to 1.0)")
    
    total_eval_latency_ms: float = Field(0.0, description="Total evaluation runtime across all samples")
    sample_results: List[SampleEvaluationResult] = Field(default_factory=list, description="Detailed per-sample evaluations")

    def format_summary_table(self) -> str:
        """Render a readable markdown summary table of the benchmark run."""
        lines = [
            f"### 📋 AeroqAI Evaluation Benchmark Report: {self.dataset_name}",
            f"- **Evaluator Engine**: `{self.evaluator_model}`",
            f"- **Total Test Cases**: `{self.total_samples}` | **Pass Rate**: `{self.pass_rate:.1f}%` ({self.passed_samples}/{self.total_samples})",
            f"- **Evaluation Latency**: `{self.total_eval_latency_ms:.2f} ms`",
            "",
            "| Metric | Average Score | Target Threshold | Status |",
            "| :--- | :---: | :---: | :---: |",
            f"| **Faithfulness (Groundedness)** | `{self.mean_faithfulness:.4f}` | `0.7000` | {'✅ PASS' if self.mean_faithfulness >= 0.7 else '❌ FAIL'} |",
            f"| **Answer Correctness** | `{self.mean_correctness:.4f}` | `0.7000` | {'✅ PASS' if self.mean_correctness >= 0.7 else '❌ FAIL'} |",
            f"| **Context Precision** | `{self.mean_context_precision:.4f}` | `0.6000` | {'✅ PASS' if self.mean_context_precision >= 0.6 else '❌ FAIL'} |",
            f"| **Overall Composite Score** | `{self.mean_overall_score:.4f}` | `0.7000` | {'✅ PASS' if self.mean_overall_score >= 0.7 else '❌ FAIL'} |"
        ]
        return "\n".join(lines)
