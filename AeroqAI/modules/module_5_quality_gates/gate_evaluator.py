"""
Module 5: Quality Regression & CI/CD Quality Gates.

Enforces absolute release thresholds and differential regression gates
to prevent degraded RAG pipelines from being deployed to production.
"""
from typing import List, Dict, Any, Optional

from AeroqAI.models.evaluation import BenchmarkReport
from AeroqAI.models.quality_gate import (
    QualityGateConfig,
    QualityGateRule,
    RuleEvaluation,
    QualityGateResult
)


class QualityGateEvaluator:
    """
    Automated evaluation engine for CI/CD Quality Gates.
    Validates evaluation benchmark reports against policy thresholds and baseline runs.
    """

    def __init__(self, config: Optional[QualityGateConfig] = None) -> None:
        self.config = config or QualityGateConfig()

    def _eval_operator(self, actual: float, operator: str, threshold: float) -> bool:
        """Evaluate numeric operator condition."""
        if operator == ">=":
            return actual >= threshold
        elif operator == "<=":
            return actual <= threshold
        elif operator == ">":
            return actual > threshold
        elif operator == "<":
            return actual < threshold
        elif operator == "==":
            return abs(actual - threshold) < 1e-4
        return False

    def evaluate_report(
        self,
        candidate_report: BenchmarkReport,
        baseline_report: Optional[BenchmarkReport] = None,
        candidate_latency_ms: Optional[float] = None
    ) -> QualityGateResult:
        """
        Evaluate candidate benchmark report against policy rules and optional baseline.
        """
        rules_to_check: List[QualityGateRule] = [
            QualityGateRule(
                metric_name="faithfulness",
                operator=">=",
                threshold=self.config.min_faithfulness,
                description="Minimum Faithfulness (Groundedness)",
                is_critical=True
            ),
            QualityGateRule(
                metric_name="answer_correctness",
                operator=">=",
                threshold=self.config.min_correctness,
                description="Minimum Answer Correctness",
                is_critical=True
            ),
            QualityGateRule(
                metric_name="context_precision",
                operator=">=",
                threshold=self.config.min_context_precision,
                description="Minimum Context Precision",
                is_critical=True
            ),
            QualityGateRule(
                metric_name="overall_quality",
                operator=">=",
                threshold=self.config.min_overall_score,
                description="Minimum Composite Triad Quality",
                is_critical=True
            ),
            QualityGateRule(
                metric_name="pass_rate",
                operator=">=",
                threshold=self.config.min_pass_rate,
                description="Minimum Benchmark Pass Rate (%)",
                is_critical=True
            ),
        ]

        if candidate_latency_ms is not None:
            rules_to_check.append(
                QualityGateRule(
                    metric_name="avg_latency_ms",
                    operator="<=",
                    threshold=self.config.max_avg_latency_ms,
                    description="Maximum Average Query Latency (ms)",
                    is_critical=False
                )
            )

        # Include custom rules
        rules_to_check.extend(self.config.custom_rules)

        # Metric mapping
        observed_metrics: Dict[str, float] = {
            "faithfulness": candidate_report.mean_faithfulness,
            "answer_correctness": candidate_report.mean_correctness,
            "correctness": candidate_report.mean_correctness,
            "context_precision": candidate_report.mean_context_precision,
            "precision": candidate_report.mean_context_precision,
            "overall_quality": candidate_report.mean_overall_score,
            "overall_score": candidate_report.mean_overall_score,
            "pass_rate": candidate_report.pass_rate,
        }
        if candidate_latency_ms is not None:
            observed_metrics["avg_latency_ms"] = candidate_latency_ms

        rule_evaluations: List[RuleEvaluation] = []
        critical_failure = False

        for rule in rules_to_check:
            actual = observed_metrics.get(rule.metric_name, 0.0)
            passed = self._eval_operator(actual, rule.operator, rule.threshold)

            msg = (
                f"{rule.metric_name}: actual {actual:.4f} {rule.operator} threshold {rule.threshold:.4f} "
                f"-> {'PASSED' if passed else 'FAILED'}"
            )

            if not passed and rule.is_critical:
                critical_failure = True

            rule_evaluations.append(
                RuleEvaluation(
                    rule=rule,
                    actual_value=actual,
                    passed=passed,
                    message=msg
                )
            )

        # Check differential regression if baseline is supplied
        regression_detected = False
        regression_delta: Optional[float] = None

        if baseline_report is not None:
            b_qual = baseline_report.mean_overall_score
            c_qual = candidate_report.mean_overall_score
            regression_delta = round(c_qual - b_qual, 4)

            # E.g. allowed drop is 0.03. If c_qual is 0.70 and b_qual is 0.80, delta is -0.10 (< -0.03) -> Regression!
            if regression_delta < -abs(self.config.max_allowable_regression):
                regression_detected = True
                critical_failure = True
                rule_evaluations.append(
                    RuleEvaluation(
                        rule=QualityGateRule(
                            metric_name="regression_tolerance",
                            operator=">=",
                            threshold=-abs(self.config.max_allowable_regression),
                            description="Regression Differential vs Baseline",
                            is_critical=True
                        ),
                        actual_value=regression_delta,
                        passed=False,
                        message=(
                            f"Candidate degraded by {abs(regression_delta):.4f}, exceeding allowable "
                            f"tolerance of {self.config.max_allowable_regression:.4f}"
                        )
                    )
                )
            else:
                rule_evaluations.append(
                    RuleEvaluation(
                        rule=QualityGateRule(
                            metric_name="regression_tolerance",
                            operator=">=",
                            threshold=-abs(self.config.max_allowable_regression),
                            description="Regression Differential vs Baseline",
                            is_critical=True
                        ),
                        actual_value=regression_delta,
                        passed=True,
                        message=f"No regression: delta {regression_delta:+.4f} is within acceptable limits"
                    )
                )

        passed_count = sum(1 for e in rule_evaluations if e.passed)
        failed_count = len(rule_evaluations) - passed_count
        overall_passed = not critical_failure

        return QualityGateResult(
            gate_name=self.config.gate_name,
            passed=overall_passed,
            total_rules_checked=len(rule_evaluations),
            passed_rules_count=passed_count,
            failed_rules_count=failed_count,
            rule_evaluations=rule_evaluations,
            regression_detected=regression_detected,
            regression_delta=regression_delta,
            benchmark_dataset=candidate_report.dataset_name
        )
