"""Data contracts and schemas for Module 5: Quality Regression & CI/CD Quality Gates."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from AeroqAI.models.evaluation import BenchmarkReport


class QualityGateRule(BaseModel):
    """Specification of an individual threshold rule."""
    metric_name: str = Field(..., description="Target metric name (e.g., faithfulness, correctness, avg_latency_ms)")
    operator: str = Field(">=", description="Comparison operator ('>=', '<=', '>', '<', '==')")
    threshold: float = Field(..., description="Numerical target threshold value")
    description: str = Field("", description="Human-readable explanation of the rule")
    is_critical: bool = Field(True, description="Whether failure of this rule halts CI/CD")


class RuleEvaluation(BaseModel):
    """Result of evaluating a single QualityGateRule."""
    rule: QualityGateRule = Field(..., description="Evaluated rule specification")
    actual_value: float = Field(..., description="Observed metric value")
    passed: bool = Field(..., description="Whether the metric satisfied the operator and threshold")
    message: str = Field(..., description="Diagnostic assessment details")


class QualityGateConfig(BaseModel):
    """Comprehensive policy configuration for CI/CD automated quality gates."""
    gate_name: str = Field("Standard RAG Release Quality Gate", description="Name of this quality gate policy")
    min_faithfulness: float = Field(0.70, description="Minimum acceptable faithfulness score (0.0 to 1.0)")
    min_correctness: float = Field(0.60, description="Minimum acceptable answer correctness score (0.0 to 1.0)")
    min_context_precision: float = Field(0.60, description="Minimum acceptable context precision score (0.0 to 1.0)")
    min_overall_score: float = Field(0.70, description="Minimum acceptable composite quality score (0.0 to 1.0)")
    min_pass_rate: float = Field(70.0, description="Minimum percentage of test samples passing the benchmark (0.0 to 100.0)")
    max_avg_latency_ms: float = Field(1500.0, description="Maximum allowable average query latency in milliseconds")
    
    # Differential Regression Protection
    max_allowable_regression: float = Field(
        0.03,
        description="Maximum allowable quality degradation compared to baseline (0.03 = 3% drop permitted)"
    )
    custom_rules: List[QualityGateRule] = Field(default_factory=list, description="Optional extra custom gate rules")


class QualityGateResult(BaseModel):
    """Complete verdict of a CI/CD Quality Gate evaluation."""
    gate_name: str = Field(..., description="Name of the evaluated quality policy")
    passed: bool = Field(..., description="Overall gate status (True = PASS release, False = BLOCK release)")
    total_rules_checked: int = Field(..., description="Count of rules evaluated")
    passed_rules_count: int = Field(..., description="Count of rules that passed")
    failed_rules_count: int = Field(..., description="Count of rules that failed")
    
    rule_evaluations: List[RuleEvaluation] = Field(default_factory=list, description="Per-rule evaluation results")
    regression_detected: bool = Field(False, description="Whether regression vs baseline exceeded tolerance")
    regression_delta: Optional[float] = Field(None, description="Quality differential vs baseline")
    benchmark_dataset: str = Field(..., description="Name of the benchmark dataset evaluated")

    def format_gate_summary(self) -> str:
        """Render a readable markdown summary table suitable for CI logs and Pull Request comments."""
        status_banner = "✅ PASSED (RELEASE APPROVED)" if self.passed else "❌ FAILED (RELEASE BLOCKED)"
        lines = [
            f"### 🛡️ AeroqAI CI/CD Quality Gate: `{self.gate_name}`",
            f"- **Verdict**: **{status_banner}**",
            f"- **Benchmark Dataset**: `{self.benchmark_dataset}`",
            f"- **Rules Summary**: `{self.passed_rules_count}/{self.total_rules_checked}` Rules Passed (`{self.failed_rules_count}` Breaches)",
        ]

        if self.regression_delta is not None:
            reg_status = "🚨 REGRESSION DETECTED" if self.regression_detected else "✅ NO REGRESSION"
            lines.append(f"- **Baseline Comparison**: Delta `{self.regression_delta:+.4f}` ({reg_status})")

        lines.extend([
            "",
            "| Rule / Metric | Operator | Threshold | Actual Value | Verdict |",
            "| :--- | :---: | :---: | :---: | :---: |"
        ])

        for ev in self.rule_evaluations:
            verdict_tag = "✅ PASS" if ev.passed else "❌ FAIL"
            lines.append(
                f"| {ev.rule.description or ev.rule.metric_name} | `{ev.rule.operator}` | "
                f"`{ev.rule.threshold}` | `{ev.actual_value:.4f}` | {verdict_tag} |"
            )

        return "\n".join(lines)
