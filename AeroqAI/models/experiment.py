"""Data contracts and schemas for Module 4: Experiment Tracking."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from AeroqAI.models.optimization import PipelineConfig
from AeroqAI.models.evaluation import BenchmarkReport


class RunMetadata(BaseModel):
    """Execution environment and versioning tags for an experiment run."""
    git_commit: Optional[str] = Field(None, description="Current Git commit SHA if in a repository")
    environment: str = Field("local", description="Runtime environment (e.g., local, dev, staging, ci)")
    user: Optional[str] = Field(None, description="User or service account that initiated the run")
    tags: Dict[str, str] = Field(default_factory=dict, description="Arbitrary custom string tags")


class RunMetrics(BaseModel):
    """Standardized performance, quality, and resource metrics for a run."""
    overall_quality_score: float = Field(..., ge=0.0, le=1.0, description="Triad composite quality score")
    faithfulness: float = Field(..., ge=0.0, le=1.0, description="Mean faithfulness score")
    answer_correctness: float = Field(..., ge=0.0, le=1.0, description="Mean factual correctness score")
    context_precision: float = Field(..., ge=0.0, le=1.0, description="Mean retrieval relevance score")
    pass_rate: float = Field(..., ge=0.0, le=100.0, description="Percentage of evaluation samples meeting the threshold")
    avg_latency_ms: float = Field(..., description="Average query latency in milliseconds")
    total_tokens_consumed: int = Field(0, description="Estimated total tokens used during evaluation")
    estimated_cost_usd: float = Field(0.0, description="Estimated cost in USD")


class ExperimentRun(BaseModel):
    """
    Comprehensive record of a single RAG pipeline experiment run.
    """
    run_id: str = Field(..., description="Unique run identifier (e.g., run_20261020_123456_a1b2)")
    experiment_name: str = Field(..., description="Group or experiment campaign name (e.g., hr_policy_tuning)")
    status: str = Field("COMPLETED", description="Run status ('RUNNING', 'COMPLETED', 'FAILED')")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC creation timestamp"
    )
    completed_at: Optional[str] = Field(None, description="ISO 8601 UTC completion timestamp")
    
    config: PipelineConfig = Field(..., description="Hyperparameter configuration used in this run")
    metrics: RunMetrics = Field(..., description="Observed quality and performance metrics")
    metadata: RunMetadata = Field(default_factory=RunMetadata, description="Runtime environment metadata")
    
    benchmark_report: Optional[BenchmarkReport] = Field(None, description="Full detailed benchmark evaluation report")
    artifact_paths: List[str] = Field(default_factory=list, description="Associated report or model artifact paths")


class RunComparison(BaseModel):
    """
    Side-by-side performance differential between a Baseline run and a Candidate run.
    """
    baseline_run_id: str = Field(..., description="Baseline benchmark run identifier")
    candidate_run_id: str = Field(..., description="Candidate benchmark run identifier")
    
    delta_quality: float = Field(..., description="Candidate overall quality minus baseline overall quality")
    delta_faithfulness: float = Field(..., description="Candidate faithfulness minus baseline faithfulness")
    delta_correctness: float = Field(..., description="Candidate correctness minus baseline correctness")
    delta_context_precision: float = Field(..., description="Candidate precision minus baseline precision")
    delta_latency_ms: float = Field(..., description="Candidate latency minus baseline latency (negative is faster)")
    delta_cost_usd: float = Field(..., description="Candidate cost minus baseline cost")
    
    is_quality_improved: bool = Field(..., description="True if candidate quality exceeds baseline")
    is_latency_improved: bool = Field(..., description="True if candidate is strictly faster than baseline")
    is_regression: bool = Field(..., description="True if candidate quality drops by more than regression tolerance")

    def format_comparison_table(self) -> str:
        """Render a readable markdown comparison scorecard."""
        def format_delta(val: float, is_better_higher: bool = True, is_pct: bool = False) -> str:
            sign = "+" if val > 0 else ""
            fmt = f"{sign}{val:.4f}" if not is_pct else f"{sign}{val:.1f}%"
            if abs(val) < 1e-4:
                return f"`{fmt}` ➖"
            is_good = (val > 0) if is_better_higher else (val < 0)
            indicator = "🟢" if is_good else "🔴"
            return f"`{fmt}` {indicator}"

        lines = [
            f"### ⚖️ AeroqAI Experiment Comparison: `{self.candidate_run_id}` vs. Baseline `{self.baseline_run_id}`",
            f"- **Quality Trend**: {'🟢 IMPROVED' if self.is_quality_improved else '🔴 REGRESSED'}",
            f"- **Speed Trend**: {'🟢 FASTER' if self.is_latency_improved else '🟡 SLOWER'}",
            f"- **Regression Flag**: {'🚨 REGRESSION DETECTED' if self.is_regression else '✅ CLEAR (NO REGRESSION)'}",
            "",
            "| Metric | Baseline | Candidate | Delta | Trend |",
            "| :--- | :---: | :---: | :---: | :---: |",
            f"| **Overall Quality** | - | - | {format_delta(self.delta_quality, is_better_higher=True)} |",
            f"| **Faithfulness** | - | - | {format_delta(self.delta_faithfulness, is_better_higher=True)} |",
            f"| **Answer Correctness** | - | - | {format_delta(self.delta_correctness, is_better_higher=True)} |",
            f"| **Context Precision** | - | - | {format_delta(self.delta_context_precision, is_better_higher=True)} |",
            f"| **Average Latency** | - | - | {format_delta(self.delta_latency_ms, is_better_higher=False)} ms |"
        ]
        return "\n".join(lines)
